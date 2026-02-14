from flask import Flask, render_template, Response, jsonify, request
import cv2
import time
import mediapipe as mp
import numpy as np
import pickle
import os
import collections
import sys
from utils import extract_keypoints

# Add local site_packages to path
sys.path.append(os.path.join(os.getcwd(), "site_packages"))

# Robust import for gTTS
try:
    from gTTS import gTTS
except ImportError:
    try:
        from gtts import gTTS
    except ImportError:
        pass

app = Flask(__name__)

MODEL_FILE = "model.p"
AUDIO_DIR = "static/audio"
CLASSES = [
    "Nothing", "Hello", "Thank You", "Good", "Bad", "Yes", 
    "Water", "Food", "Toilet", "Medicine", "Money", 
    "Help", "Pain", "Call Doctor", "Police", "Home", 
    "What", "Where", "Time", "I Love You", "Stop",
    "No", "Please", "Sorry", "Friend", "Mother", 
    "Book", "Tea", "Name", "Happy" 
]

# --- LOAD MODEL (Robustly) ---
try:
    with open(MODEL_FILE, "rb") as f:
        model_dict = pickle.load(f)
        model = model_dict['model']
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# --- CONFIGURATION ---
PREDICTION_BUFFER_SIZE = 3  # Reduced buffer size for better responsiveness
AUDIO_COOLDOWN = 3.0        # Seconds to wait before playing same audio again
CONFIDENCE_THRESHOLD = 0.5

# --- GLOBAL STATE ---
prediction_buffer = collections.deque(maxlen=PREDICTION_BUFFER_SIZE)
current_prediction = "Nothing"
last_sent_prediction = "Nothing"
last_audio_time = 0
last_heartbeat_time = time.time()

# --- MEDIAPIPE SETUP ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def draw_robotic_hands(image, hand_landmarks):
    h, w, c = image.shape
    
    # Define connections directly from MediaPipe
    connections = mp_hands.HAND_CONNECTIONS
    
    # Colors (BGR) for Cyberpunk Theme
    COLOR_NEON_GREEN = (57, 255, 20)    # Neon Green
    COLOR_CYAN = (255, 255, 0)          # Cyan
    COLOR_ELECTRIC_BLUE = (255, 128, 0) # Blue-ish
    COLOR_WHITE = (255, 255, 255)

    # 1. Draw Connections (Energy Beams)
    for connection in connections:
        start_idx = connection[0]
        end_idx = connection[1]
        
        start_point = (int(hand_landmarks.landmark[start_idx].x * w), int(hand_landmarks.landmark[start_idx].y * h))
        end_point = (int(hand_landmarks.landmark[end_idx].x * w), int(hand_landmarks.landmark[end_idx].y * h))
        
        # Glow Effect (Layers)
        cv2.line(image, start_point, end_point, COLOR_ELECTRIC_BLUE, 4) # Outer Glow
        cv2.line(image, start_point, end_point, COLOR_CYAN, 2)          # Inner Core
        
    # 2. Draw Landmarks (Tech Nodes)
    for idx, landmark in enumerate(hand_landmarks.landmark):
        cx, cy = int(landmark.x * w), int(landmark.y * h)
        
        # Size varies slightly by landmark type (Tips are larger)
        radius = 5
        if idx in [4, 8, 12, 16, 20]: # Fingertips
            radius = 8
            
        # Draw Node
        cv2.circle(image, (cx, cy), radius + 2, COLOR_ELECTRIC_BLUE, 1) # Outer Ring
        cv2.circle(image, (cx, cy), radius, COLOR_NEON_GREEN, -1)       # Filled Core
        cv2.circle(image, (cx, cy), 2, COLOR_WHITE, -1)                 # Highlight Center

def gen_frames():
    global current_prediction, last_heartbeat_time
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Could not open webcam.")
        return

    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        max_num_hands=2
    ) as hands:
        
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Mirror the image
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            
            # Draw landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Use Custom Robotic Drawing
                    try:
                        draw_robotic_hands(frame, hand_landmarks)
                    except Exception as e:
                        print(f"⚠️ Drawing Error: {e}")
                        # Fallback to default
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # --- PREDICTION LOGIC ---
            raw_prediction = "Nothing"
            
            if results.multi_hand_landmarks and model is not None:
                try:
                    # distinct extract_keypoints function from utils.py
                    data_aux = extract_keypoints(results)
                    
                    # Make Prediction
                    # Model returns string labels directly (e.g., 'Water', 'Nothing')
                    prediction_result = model.predict([data_aux])[0]
                    
                    if isinstance(prediction_result, str):
                        if prediction_result.lower() == "bus":
                             raw_prediction = "Nothing"
                        else:
                             raw_prediction = prediction_result
                    else:
                        # Fallback for older models (index based)
                        prediction_index = int(prediction_result)
                        if 0 <= prediction_index < len(CLASSES):
                            raw_prediction = CLASSES[prediction_index]
                        else:
                            print(f"⚠️ Prediction index {prediction_index} out of bounds.")
                            
                except Exception as e:
                    print(f"⚠️ Prediction Error: {e}")

            # --- STABILITY LOGIC (ACTIVE) ---
            prediction_buffer.append(raw_prediction)
            
            # Only update if the buffer is FULL of the SAME prediction
            if len(prediction_buffer) == PREDICTION_BUFFER_SIZE:
                if len(set(prediction_buffer)) == 1: # All elements are same
                    if current_prediction != prediction_buffer[0]:
                        current_prediction = prediction_buffer[0]
                        print(f"👉 [GESTURE] Verified: {current_prediction}") # Log Gesture Change
            
            # Fallback: If buffer isn't unanimous, keep old prediction (reduces flicker)
            # --- END STABILITY LOGIC ---

            # Heartbeat Log (Every 20 seconds)
            if (time.time() - last_heartbeat_time) > 20:
                print(f"💓 [HEARTBEAT] System Active - Last Prediction: {current_prediction}")
                last_heartbeat_time = time.time()
                
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route('/log_event')
def log_event():
    msg = request.args.get('msg', 'Unknown Event')
    print(f"👆 [TOUCH] {msg}")
    return jsonify({"status": "logged"})

BENGALI_MAP = {
    "Nothing": "", "Hello": "নমস্কার", "Thank You": "ধন্যবাদ", "Good": "খুব ভালো", "Bad": "খারাপ", "Yes": "হ্যাঁ", 
    "Water": "আমার জল লাগবে", "Food": "আমার খাবার লাগবে", "Toilet": "আমি টয়লেটে যাবো", "Medicine": "আমার ওষুধ লাগবে", 
    "Money": "আমার টাকা লাগবে", "Help": "সাহায্য করুন", "Pain": "আমার ব্যথা করছে", "Call Doctor": "ডাক্তার ডাকুন", 
    "Police": "পুলিশ ডাকুন", "Home": "আমি বাড়ি যাবো", "What": "কী?", "Where": "কোথায়?", "Time": "কটা বাজে?", 
    "I Love You": "আমি তোমাকে ভালোবাসি", "Stop": "থামুন", "No": "না", "Please": "দয়া করে", "Sorry": "ক্ষমা করুন", 
    "Friend": "বন্ধু", "Mother": "মা", "Book": "বই", "Tea": "আমি চা খাবো", "Name": "আমার নাম", "Happy": "আমি খুব খুশি"
}

HINDI_MAP = {
    "Nothing": "", "Hello": "नमस्ते", "Thank You": "धन्यवाद", "Good": "बहुत अच्छा", "Bad": "खराब", "Yes": "हाँ", 
    "Water": "मुझे पानी चाहिए", "Food": "मुझे खाना चाहिए", "Toilet": "मुझे वॉशरूम जाना है", "Medicine": "मुझे दवाई चाहिए", 
    "Money": "मुझे पैसे चाहिए", "Help": "मेरी मदद करें", "Pain": "मुझे दर्द हो रहा है", "Call Doctor": "डॉक्टर को बुलाओ", 
    "Police": "पुलिस को बुलाओ", "Home": "मुझे घर जाना है", "What": "क्या?", "Where": "कहाँ?", "Time": "समय क्या हुआ है?", 
    "I Love You": "मैं तुमसे प्यार करता हूँ", "Stop": "रुकिए", "No": "नहीं", "Please": "कृपया", "Sorry": "माफ़ करें", 
    "Friend": "दोस्त", "Mother": "माँ", "Book": "किताब", "Tea": "मुझे चाय चाहिए", "Name": "मेरा नाम", "Happy": "मैं बहुत खुश हूँ"
}

ENGLISH_MAP = {
    "Nothing": "", "Hello": "Hello", "Thank You": "Thank you", "Good": "Good", "Bad": "Bad", "Yes": "Yes", 
    "Water": "I need water", "Food": "I need food", "Toilet": "I need the washroom", "Medicine": "I need medicine", 
    "Money": "I need money", "Help": "Help me", "Pain": "I am in pain", "Call Doctor": "Call a doctor", 
    "Police": "Call the police", "Home": "I want to go home", "What": "What?", "Where": "Where?", "Time": "What time is it?", 
    "I Love You": "I love you", "Stop": "Stop", "No": "No", "Please": "Please", "Sorry": "Sorry", "Friend": "Friend", 
    "Mother": "Mother", "Book": "Book", "Tea": "I want tea", "Name": "My name is", "Happy": "I am happy"
}

# --- POLITE / FORMAL MAPS ---
BENGALI_POLITE_MAP = {
    "Nothing": "", "Hello": "আপনাকে নমস্কার", "Thank You": "আপনাকে অনেক ধন্যবাদ", "Good": "এটি খুব ভালো", "Bad": "এটি ঠিক নয়", "Yes": "আজ্ঞে হ্যাঁ", 
    "Water": "দয়া করে আমাকে একটু জল দেবেন?", "Food": "দয়া করে আমাকে একটু খাবার দেবেন?", "Toilet": "শৌচালয়টি কোনদিকে বলতে পারবেন?", 
    "Medicine": "আমার একটু ওষুধের প্রয়োজন ছিল", "Money": "আমার কিছু টাকার প্রয়োজন ছিল", "Help": "ক্ষমা করবেন, আমাকে একটু সাহায্য করতে পারবেন?", 
    "Pain": "আমার শরীরে খুব ব্যথা করছে", "Call Doctor": "দয়া করে একজন ডাক্তার ডেকে দিন", "Police": "অনুগ্রহ করে পুলিশকে খবর দিন", 
    "Home": "আমি বাড়ি ফিরে যেতে চাই", "What": "এটি কী বলতে পারবেন?", "Where": "এটি কোথায় বলতে পারবেন?", "Time": "দয়া করে কটা বাজে বলবেন?", 
    "I Love You": "আমি আপনাকে শ্রদ্ধা করি", "Stop": "দয়া করে এবার থামুন", "No": "আজ্ঞে না", "Please": "অনুগ্রহ করে", "Sorry": "দয়া করে আমাকে ক্ষমা করবেন", 
    "Friend": "আপনি আমার বন্ধু", "Mother": "মা", "Book": "আমি বইটি পড়তে চাই", "Tea": "দয়া করে আমাকে এক কাপ চা দেবেন?", "Name": "আমার নাম হলো", "Happy": "আমি আজ অত্যন্ত আনন্দিত"
}

HINDI_POLITE_MAP = {
    "Nothing": "", "Hello": "आपको नमस्कार", "Thank You": "आपका बहुत बहुत धन्यवाद", "Good": "यह बहुत अच्छा है", "Bad": "यह ठीक नहीं है", "Yes": "जी हाँ", 
    "Water": "क्या मुझे कृपया थोड़ा पानी मिल सकता है?", "Food": "क्या मुझे कृपया थोड़ा खाना मिल सकता है?", "Toilet": "क्षमा करें, वॉशरूम किस तरफ है?", 
    "Medicine": "मुझे कुछ दवाइयों की आवश्यकता है", "Money": "मुझे कुछ पैसों की आवश्यकता है", "Help": "माफ़ कीजिए, क्या आप मेरी मदद कर सकते हैं?", 
    "Pain": "मुझे बहुत दर्द महसूस हो रहा है", "Call Doctor": "कृपया एक डॉक्टर को बुला दीजिए", "Police": "कृपया पुलिस को सूचित करें", 
    "Home": "मैं अपने घर लौटना चाहता हूँ", "What": "क्या आप बता सकते हैं यह क्या है?", "Where": "क्या आप बता सकते हैं यह कहाँ है?", "Time": "कृपया बताएँगे कि समय क्या हुआ है?", 
    "I Love You": "मैं आपका आदर करता हूँ", "Stop": "कृपया अब रुक जाइए", "No": "जी नहीं", "Please": "कृपया", "Sorry": "कृपया मुझे माफ़ कर दीजिए", 
    "Friend": "आप मेरे मित्र हैं", "Mother": "माता जी", "Book": "मैं यह किताब पढ़ना चाहता हूँ", "Tea": "क्या मुझे एक कप चाय मिल सकती है?", "Name": "मेरा शुभ नाम है", "Happy": "मैं आज बहुत प्रसन्न हूँ"
}

ENGLISH_POLITE_MAP = {
    "Nothing": "", "Hello": "Greetings to you", "Thank You": "Thank you so much", "Good": "This is very good", "Bad": "I don't think this is right", "Yes": "Yes, please", 
    "Water": "Excuse me, could I please have some water?", "Food": "Could I please get something to eat?", "Toilet": "Could you please tell me where the washroom is?", 
    "Medicine": "I am in need of some medicine, please", "Money": "I require some financial assistance, please", "Help": "Excuse me, would you be able to help me?", 
    "Pain": "I am experiencing severe pain", "Call Doctor": "Could you please call a doctor for me?", "Police": "Please inform the police immediately", 
    "Home": "I would like to return home now", "What": "Could you please explain what this is?", "Where": "Could you please tell me where this is?", "Time": "Excuse me, could you tell me the time?", 
    "I Love You": "I have great respect for you", "Stop": "Could you please stop now?", "No": "No, thank you", "Please": "If you please", "Sorry": "I sincerely apologize", 
    "Friend": "You are a good friend", "Mother": "Mother", "Book": "I would like to read this book", "Tea": "Could I please have a cup of tea?", "Name": "My name is", "Happy": "I am delighted"
}


@app.route('/status')
def status():
    global last_sent_prediction, current_prediction, last_audio_time
    
    # Get parameters from the frontend URL
    lang = request.args.get('lang', 'bengali')
    is_polite = request.args.get('polite', 'false') == 'true'
    
    # 1. Select the correct Dictionary based on Language AND Polite toggle
    if lang == 'hindi':
        active_map = HINDI_POLITE_MAP if is_polite else HINDI_MAP
    elif lang == 'english':
        active_map = ENGLISH_POLITE_MAP if is_polite else ENGLISH_MAP
    else:
        active_map = BENGALI_POLITE_MAP if is_polite else BENGALI_MAP

    sentence = active_map.get(current_prediction, "")
    resp = {"prediction": current_prediction, "sentence": sentence, "new_gesture": False, "audio_url": ""}
    
    # 2. Logic to play audio (With Cooldown)
    current_time = time.time()
    if current_prediction != last_sent_prediction:
        # Check cooldown (avoid rapid firing)
        if (current_time - last_audio_time) > AUDIO_COOLDOWN:
            resp["new_gesture"] = True
            last_sent_prediction = current_prediction
            last_audio_time = current_time # Update timer
            
            if current_prediction != "Nothing":
                # Direct the frontend to the correct folder
                folder_name = f"{lang}_polite" if is_polite else lang
                # Normalize filename to match file system: "Call Doctor" -> "call_doctor"
                normalized_filename = current_prediction.lower().replace(" ", "_")
                resp["audio_url"] = f"/static/audio/{folder_name}/{normalized_filename}.mp3"
            
    return jsonify(resp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
