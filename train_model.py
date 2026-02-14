import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

DATA_FILE = "data.csv"
MODEL_FILE = "model.p"

def train_model():
    print("Loading data...")
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found. Run data_collector.py first!")
        return

    # Check if data is empty
    if df.empty:
        print("Error: Data file is empty.")
        return

    print(f"Data shape: {df.shape}")
    print(f"Classes found: {df['label'].unique()}")

    # Prepare features (X) and labels (y)
    # Columns are label, x0, y0, z0, ...
    X = df.drop('label', axis=1) # All columns except label
    y = df['label']

    # --- Data Augmentation ---
    print("Applying Data Augmentation (Noise Injection)...")
    # Add Gaussian noise
    noise_factor = 0.05
    X_noisy = X + np.random.normal(0, noise_factor, X.shape)
    X_noisy_2 = X + np.random.normal(0, noise_factor * 2, X.shape) # Stronger noise

    # Concatenate original + augmented data
    X_aug = pd.concat([X, X_noisy, X_noisy_2], ignore_index=True)
    y_aug = pd.concat([y, y, y], ignore_index=True)
    
    print(f"Original samples: {len(X)}")
    print(f"Augmented samples: {len(X_aug)}")

    # Use Augmented Data for training
    X, y = X_aug, y_aug

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True, stratify=y)

    # Train Random Forest
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, n_jobs=-1)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")
    
    # Save model
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump({'model': model}, f)
    
    print(f"Model saved to {MODEL_FILE}")

    # Optional: Confusion Matrix
    # cm = confusion_matrix(y_test, y_pred)
    # print("Confusion Matrix:\n", cm)

if __name__ == "__main__":
    train_model()
