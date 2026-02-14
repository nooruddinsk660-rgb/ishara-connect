import cv2
import mediapipe as mp
import numpy as np

def extract_keypoints(results):
    """
    Extracts normalized landmarks from both hands.
    - Centers coordinates relative to the WRIST.
    - Scales coordinates based on hand size (WRIST to MIDDLE_MCP distance).
    - Returns a flattened list of 126 values (63 for Left, 63 for Right).
    - If a hand is missing, fills with zeros.
    """
    # 21 landmarks * 3 coords (x,y,z) = 63 values per hand
    lh = np.zeros(21 * 3)
    rh = np.zeros(21 * 3)

    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # MediaPipe classification: "Left" or "Right"
            # Note: In selfie view, "Left" is usually your actual right hand, but we keep the label consistent.
            label = handedness.classification[0].label
            
            # 1. Get Landmarks as array
            landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
            
            # 2. Centering: Subtract Wrist (Landmark 0)
            wrist = landmarks[0]
            centered = landmarks - wrist
            
            # 3. Scaling: Normalize by distance between Wrist(0) and Middle MCP(9)
            # This makes the features invariant to camera distance/hand size.
            # We use a small epsilon to avoid division by zero.
            middle_mcp = landmarks[9]
            scale = np.linalg.norm(middle_mcp - wrist)
            if scale < 1e-6: scale = 1.0 # Fallback
            
            normalized = centered / scale
            
            # Flatten
            flat_hand = normalized.flatten()

            # Assign to correct slot
            if label == 'Left':
                lh = flat_hand
            else:
                rh = flat_hand

    # Concatenate Left + Right
    return np.concatenate([lh, rh])
