import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
import sys
import argparse
import time
import uuid

from utils import extract_keypoints

# --- Configuration ---
DATA_FILE = "data.csv"
FRAMES_PER_CLASS = 500

CLASSES_FULL = [
    "Nothing", "Hello", "Thank You", "Good", "Bad", "Yes",
    "Water", "Food", "Toilet", "Medicine", "Money",
    "Help", "Pain", "Call Doctor", "Police", "Home",
    "What", "Where", "Time", "I Love You", "Stop",
    "No", "Please", "Sorry", "Friend", "Mother",
    "Book", "Tea", "Name", "Happy"
]

parser = argparse.ArgumentParser(description="Ishara-Connect Hand Gesture Data Collector")
parser.add_argument('--classes', nargs='*', default=[], help='Target classes to record (default: all 30 classes)')
parser.add_argument('--signer_id', type=str, default=None,
                     help="Unique name/ID for whoever is signing in this run, e.g. 'noor', 'ankita'.")
parser.add_argument('--session_note', type=str, default='unspecified',
                     help="Free-text context for this recording run: lighting, camera, handedness.")
parser.add_argument('--frames', type=int, default=500, help='Number of frames to record per class (default: 500)')
parser.add_argument('--reset', action='store_true', help='Reset/clear existing data.csv and start completely fresh')
parser.add_argument('--resume', action='store_true',
                     help='Auto-resume from remaining unrecorded classes for this signer')
args, _ = parser.parse_known_args()

FRAMES_PER_CLASS = args.frames
TARGET_CLASSES = args.classes

if args.reset and os.path.exists(DATA_FILE):
    backup_file = f"data_backup_{int(time.time())}.csv"
    os.rename(DATA_FILE, backup_file)
    print(f"📦 Existing {DATA_FILE} backed up to {backup_file}")

SIGNER_ID = args.signer_id
if not SIGNER_ID:
    try:
        user_input = input("Enter Signer Name / ID (e.g. noor) [default: signer_1]: ").strip()
        SIGNER_ID = user_input if user_input else "signer_1"
    except (EOFError, KeyboardInterrupt):
        SIGNER_ID = "signer_1"

SESSION_NOTE = args.session_note
SESSION_ID = f"{SIGNER_ID}_{int(time.time())}_{uuid.uuid4().hex[:6]}"

# Determine classes to record
if TARGET_CLASSES:
    CLASSES = TARGET_CLASSES
elif args.resume and os.path.exists(DATA_FILE):
    try:
        df_existing = pd.read_csv(DATA_FILE)
        if 'signer_id' in df_existing.columns:
            done_labels = set(df_existing[df_existing['signer_id'] == SIGNER_ID]['label'].unique())
        else:
            done_labels = set(df_existing['label'].unique())
        CLASSES = [c for c in CLASSES_FULL if c not in done_labels]
        print(f"🔄 Resuming for signer '{SIGNER_ID}'. {len(done_labels)} already recorded. {len(CLASSES)} remaining classes.")
    except Exception as e:
        CLASSES = CLASSES_FULL
else:
    CLASSES = CLASSES_FULL

META_COLS = ['label', 'signer_id', 'session_id', 'session_note']

# --- MediaPipe Setup ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils


def _landmark_cols():
    cols = []
    for hand in ['lh', 'rh']:
        for i in range(21):
            cols.extend([f'{hand}_x{i}', f'{hand}_y{i}', f'{hand}_z{i}'])
    return cols


def _migrate_legacy(df):
    """Older data.csv files (collected before this fix) only have 'label' +
    landmark columns. Tag every existing row as one legacy signer/session
    instead of dropping it -- it's still real single-signer data, just
    unlabeled until now."""
    if 'signer_id' not in df.columns:
        print("Note: existing data.csv predates signer tracking -- tagging all "
              "prior rows as 'legacy_unknown_signer' / 'legacy_session'.")
        df = df.assign(signer_id='legacy_unknown_signer', session_id='legacy_session',
                       session_note='legacy_pre_signer_tracking')
    return df


def save_data(label, new_data):
    cols = META_COLS + _landmark_cols()
    new_df = pd.DataFrame(new_data, columns=cols)

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = _migrate_legacy(df)
        # Only remove THIS signer's PREVIOUS take of THIS exact label (lets someone
        # redo a bad recording). Every other signer's data for this label is kept --
        # this is the actual fix: the old version deleted ALL rows for the label,
        # regardless of who recorded them.
        before = len(df)
        df = df[~((df['label'] == label) & (df['signer_id'] == SIGNER_ID))]
        removed = before - len(df)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        if removed:
            print(f"[REDO] Replaced {SIGNER_ID}'s previous '{label}' take ({removed} frames) "
                  f"with {len(new_data)} new frames. Other signers' data for '{label}' untouched.")
        else:
            print(f"[ADDED] {SIGNER_ID}: +{len(new_data)} frames for '{label}'.")
    else:
        new_df.to_csv(DATA_FILE, index=False)
        print(f"[CREATED] data.csv -- {SIGNER_ID}: {len(new_data)} frames for '{label}'.")


def print_diversity_report():
    if not os.path.exists(DATA_FILE):
        return
    df = pd.read_csv(DATA_FILE)
    df = _migrate_legacy(df)
    print("\n--- Signer diversity so far ---")
    report = df.groupby('label')['signer_id'].nunique().sort_values()
    for label, n_signers in report.items():
        flag = "  <-- still single-signer" if n_signers < 2 else ""
        print(f"  {label:15s} {n_signers} signer(s){flag}")
    print("--------------------------------\n")


def main():
    print("=== Ishara-Connect: 2-Hand Data Collector ===")
    print(f"Signer: {SIGNER_ID} | Session: {SESSION_ID} | Note: {SESSION_NOTE}\n")

    cap = cv2.VideoCapture(0)
    current_class_index = 0
    recording = False
    frames_recorded = 0
    data_buffer = []
    target_label = CLASSES[0] if CLASSES else None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if current_class_index < len(CLASSES):
            target_label = CLASSES[current_class_index]
            cv2.putText(frame, f"Signer: {SIGNER_ID} | Target: {target_label} ({current_class_index + 1}/{len(CLASSES)})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            if recording:
                cv2.putText(frame, f"REC: {frames_recorded}/{FRAMES_PER_CLASS}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                keypoints = extract_keypoints(results)
                data_buffer.append([target_label, SIGNER_ID, SESSION_ID, SESSION_NOTE] + keypoints.tolist())
                frames_recorded += 1

                if frames_recorded >= FRAMES_PER_CLASS:
                    save_data(target_label, data_buffer)
                    recording = False
                    frames_recorded = 0
                    data_buffer = []
                    current_class_index += 1
                    print(f"Finished {target_label}. Next class...")
            else:
                cv2.putText(frame, "Press 'R' to Record", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        else:
            cv2.putText(frame, "DONE! Press 'Q'", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("2-Hand Collector", frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        if key == ord('r') and not recording and current_class_index < len(CLASSES):
            print(f"Starting recording for {target_label}...")
            recording = True
            frames_recorded = 0
            data_buffer = []

    cap.release()
    cv2.destroyAllWindows()
    print_diversity_report()


if __name__ == "__main__":
    main()
