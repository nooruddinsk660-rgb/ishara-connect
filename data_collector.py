import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os

# --- Configuration ---
DATA_FILE = "data.csv"
FRAMES_PER_CLASS = 500
# --- TARGETED RETRAINING LIST ---
# If you want to retake specific gestures, uncomment the list below.
# OTHERWISE, IT WILL CYCLE THROUGH ALL 30 CLASSES.
# TARGET_CLASSES = ["Bad", "Time", "Pain", "Friend"] 
# TARGET_CLASSES = ["Bad", "Time", "Pain", "Friend"] 
# TARGET_CLASSES = ["Thank You", "Good", "Money"] # Set to empty list [] to record ALL classes
TARGET_CLASSES = ["Name"]
CLASSES_FULL = [
    "Nothing", "Hello", "Thank You", "Good", "Bad", "Yes", 
    "Water", "Food", "Toilet", "Medicine", "Money", 
    "Help", "Pain", "Call Doctor", "Police", "Home", 
    "What", "Where", "Time", "I Love You", "Stop",
    "No", "Please", "Sorry", "Friend", "Mother", 
    "Book", "Tea", "Name", "Happy"
]

# Use Target List if not empty
CLASSES = TARGET_CLASSES if TARGET_CLASSES else CLASSES_FULL

# --- MediaPipe Setup ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,  # <--- CHANGED TO 2
    min_detection_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

from utils import extract_keypoints

# --- Configuration ---

def save_data(label, new_data):
    # Columns definition
    cols = ['label']
    for hand in ['lh', 'rh']:
        for i in range(21):
            cols.extend([f'{hand}_x{i}', f'{hand}_y{i}', f'{hand}_z{i}'])
            
    new_df = pd.DataFrame(new_data, columns=cols)
    
    if os.path.exists(DATA_FILE):
        # Read existing data
        df = pd.read_csv(DATA_FILE)
        # Remove OLD rows for this specific label (Overwrite logic)
        df = df[df['label'] != label]
        # Append NEW data
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        print(f"[UPDATED] Overwrote {label} with {len(new_data)} new frames.")
    else:
        new_df.to_csv(DATA_FILE, index=False)
        print(f"[CREATED] Saved {len(new_data)} frames for {label}")

def main():
    cap = cv2.VideoCapture(0)
    print("=== Ishara-Connect: 2-Hand Data Collector ===")
    
    current_class_index = 0
    recording = False
    frames_recorded = 0
    data_buffer = []

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1) # Mirror effect
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        # Draw Landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # UI Logic
        if current_class_index < len(CLASSES):
            target_label = CLASSES[current_class_index]
            cv2.putText(frame, f"Target: {target_label} ({current_class_index + 1}/{len(CLASSES)})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if recording:
                cv2.putText(frame, f"REC: {frames_recorded}/{FRAMES_PER_CLASS}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Extract Data
                keypoints = extract_keypoints(results)
                data_buffer.append([target_label] + keypoints.tolist())
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
        if key == ord('q'): break
        if key == ord('r') and not recording and current_class_index < len(CLASSES):
             print(f"Starting recording for {target_label} in 3 seconds...")
             recording = True
             frames_recorded = 0
             data_buffer = [] # Ensure buffer is clean

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
