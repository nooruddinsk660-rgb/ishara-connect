import pandas as pd
import numpy as np
import pickle
import datetime
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from db import DB_ENABLED, SessionLocal, init_db
from models import ModelVersion, utcnow

DATA_FILE = "data.csv"
MODEL_FILE = "model.p"
TEST_SIZE = 0.2
RANDOM_STATE = 42

META_COLS = ['label', 'signer_id', 'session_id', 'session_note']


def _migrate_legacy(df):
    if 'signer_id' not in df.columns:
        print("Note: data.csv predates signer/session tracking (pre-fix format). "
              "Tagging all rows as one legacy signer/session -- every metric below "
              "is effectively single-signer and will read higher than real-world "
              "accuracy. Re-collect with the current data_collector.py for honest numbers.")
        df = df.assign(signer_id='legacy_unknown_signer', session_id='legacy_session',
                       session_note='legacy_pre_signer_tracking')
    return df


def diversity_report(df):
    print("\n--- Data diversity (before split) ---")
    per_label = df.groupby('label').agg(
        signers=('signer_id', 'nunique'),
        sessions=('session_id', 'nunique'),
        frames=('label', 'count')
    ).sort_values('sessions')
    for label, row in per_label.iterrows():
        flag = "  <-- 1 session, test score for this class will be optimistic" if row['sessions'] < 2 else ""
        print(f"  {label:15s} signers={int(row['signers'])} sessions={int(row['sessions'])} frames={int(row['frames'])}{flag}")
    print("--------------------------------------\n")


def group_aware_split(df):
    """Split by session_id so frames from the same continuous recording take
    never appear in both train and test (they're near-duplicates a few
    milliseconds apart -- letting them split across sets is what inflated the
    original accuracy number). Labels that only have one session so far can't
    be group-split without losing that class entirely from one side, so those
    fall back to a random row-level split -- flagged clearly, since that
    number is still optimistic until a 2nd session/signer exists."""
    train_parts, test_parts = [], []
    single_session_labels = set()

    for label, group in df.groupby('label'):
        n_sessions = group['session_id'].nunique()
        if n_sessions >= 2:
            splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
            train_idx, test_idx = next(splitter.split(group, groups=group['session_id']))
            train_parts.append(group.iloc[train_idx])
            test_parts.append(group.iloc[test_idx])
        else:
            single_session_labels.add(label)
            shuffled = group.sample(frac=1, random_state=RANDOM_STATE)
            cut = max(1, int(len(shuffled) * (1 - TEST_SIZE)))
            train_parts.append(shuffled.iloc[:cut])
            test_parts.append(shuffled.iloc[cut:])

    train_df = pd.concat(train_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)
    return train_df, test_df, single_session_labels


def augment(X, y, noise_factor=0.05):
    X_noisy = X + np.random.normal(0, noise_factor, X.shape)
    X_noisy_2 = X + np.random.normal(0, noise_factor * 2, X.shape)
    X_aug = pd.concat([X, X_noisy, X_noisy_2], ignore_index=True)
    y_aug = pd.concat([y, y, y], ignore_index=True)
    return X_aug, y_aug


def train_model():
    print("Loading data...")
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found. Run data_collector.py first!")
        return

    if df.empty:
        print("Error: Data file is empty.")
        return

    df = _migrate_legacy(df)
    print(f"Data shape: {df.shape}")
    print(f"Classes found: {sorted(df['label'].unique())}")

    diversity_report(df)

    # --- Split BEFORE augmenting, grouped by recording session ---
    train_df, test_df, single_session_labels = group_aware_split(df)

    feature_cols = [c for c in df.columns if c not in META_COLS]
    X_train, y_train = train_df[feature_cols], train_df['label']
    X_test, y_test = test_df[feature_cols], test_df['label']

    print(f"Train frames: {len(X_train)} | Test frames: {len(X_test)} (test set is never augmented)")

    # --- Augment training data only ---
    print("Applying data augmentation (noise injection) to the TRAINING split only...")
    X_train, y_train = augment(X_train, y_train)
    print(f"Augmented training samples: {len(X_train)}")

    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nHeld-out accuracy (session-grouped split, no leakage): {accuracy * 100:.2f}%")
    if single_session_labels:
        print(f"{len(single_session_labels)} class(es) are still single-session: {sorted(single_session_labels)}")
        print("Their contribution to the number above is optimistic -- collect a 2nd session/signer for them "
              "before quoting this number to anyone outside the team.")

    with open(MODEL_FILE, 'wb') as f:
        pickle.dump({
            'model': model,
            'accuracy': accuracy,
            'classes': sorted(df['label'].unique().tolist()),
            'version': '1.3',
            'trained_at': datetime.datetime.now().isoformat(),
            'single_session_labels': sorted(single_session_labels),
            'signers': sorted(df['signer_id'].unique().tolist()),
        }, f)

    print(f"Model saved to {MODEL_FILE}")

    # --- Stage 1: also record this training run in Postgres, if configured ---
    if DB_ENABLED:
        try:
            init_db()
            db = SessionLocal()
            db.add(ModelVersion(
                type='rf',
                version='1.3',
                accuracy=accuracy,
                trained_at=utcnow(),  # UTC, consistent with sessions/transcript_events
                artifact_path=MODEL_FILE,
            ))
            db.commit()
            db.close()
            print("Training run recorded in Postgres (model_versions).")
        except Exception as e:
            print(f"⚠️ [DB] Could not record model_versions row: {e}")
    else:
        print("DATABASE_URL not set -- skipping model_versions logging (model.p still saved normally).")

    # Optional: Confusion Matrix
    # cm = confusion_matrix(y_test, y_pred)
    # sns.heatmap(cm, annot=True)
    # plt.show()


if __name__ == "__main__":
    train_model()
