import base64
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import time
import mediapipe as mp
import numpy as np
import pickle
import os
import collections
import json
import sys
import threading
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32))
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CONFIGURATION ---
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

PREDICTION_BUFFER_SIZE = 3  # Reduced buffer size for better responsiveness
AUDIO_COOLDOWN = 3.0        # Seconds to wait before playing same audio again
CONFIDENCE_THRESHOLD = 0.5

# --- GLOBAL STATE & LOCKS ---
state_lock = threading.Lock()
model = None

# Store state per socket session ID
user_sessions = {}

# --- LOAD MODEL (Robustly) ---
try:
    with open(MODEL_FILE, "rb") as f:
        model_dict = pickle.load(f)
        model = model_dict['model']
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")

# --- LOAD TRANSLATIONS ---
translations = {}
for lang in ['bengali', 'hindi', 'english']:
    try:
        with open(f"translations/{lang}.json", "r", encoding="utf-8") as f:
            translations[lang] = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {lang} translations: {e}")
        translations[lang] = {"standard": {}, "polite": {}}

# --- BACKGROUND AUDIO GENERATOR ---
def generate_audio_background(text, lang_code, full_path, url):
    """Generate audio in a separate thread and emit event when done."""
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(full_path)
        print(f"✅ [BG] Audio Generated: {full_path}")
        # Notify clients audio is ready
        socketio.emit('play_audio', {'audio_url': url})
    except Exception as e:
        print(f"❌ [BG] TTS Error: {e}")

def get_active_map(lang='bengali', polite=False):
    t_type = "polite" if polite else "standard"
    lang_code_map = {'hindi': 'hi', 'english': 'en', 'bengali': 'bn'}
    return translations.get(lang, {}).get(t_type, {}), lang_code_map.get(lang, 'bn')

# --- MEDIAPIPE SETUP ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def draw_robotic_hands(image, hand_landmarks):
    h, w, c = image.shape
    connections = mp_hands.HAND_CONNECTIONS
    
    # Colors (BGR) for Cyberpunk Theme
    COLOR_NEON_GREEN = (57, 255, 20)
    COLOR_CYAN = (255, 255, 0)
    COLOR_ELECTRIC_BLUE = (255, 128, 0)
    COLOR_WHITE = (255, 255, 255)

    # 1. Draw Connections (Energy Beams)
    for connection in connections:
        start_idx = connection[0]
        end_idx = connection[1]
        start_point = (int(hand_landmarks.landmark[start_idx].x * w), int(hand_landmarks.landmark[start_idx].y * h))
        end_point = (int(hand_landmarks.landmark[end_idx].x * w), int(hand_landmarks.landmark[end_idx].y * h))
        cv2.line(image, start_point, end_point, COLOR_ELECTRIC_BLUE, 4)
        cv2.line(image, start_point, end_point, COLOR_CYAN, 2)
        
    # 2. Draw Landmarks (Tech Nodes)
    for idx, landmark in enumerate(hand_landmarks.landmark):
        cx, cy = int(landmark.x * w), int(landmark.y * h)
        radius = 8 if idx in [4, 8, 12, 16, 20] else 5
        cv2.circle(image, (cx, cy), radius + 2, COLOR_ELECTRIC_BLUE, 1)
        cv2.circle(image, (cx, cy), radius, COLOR_NEON_GREEN, -1)
        cv2.circle(image, (cx, cy), 2, COLOR_WHITE, -1)

def gen_frames():
    prediction_buffer = collections.deque(maxlen=PREDICTION_BUFFER_SIZE)
    current_prediction = "Nothing"
    last_sent_prediction = "Nothing"
    last_audio_time = 0
    last_heartbeat_time = time.time()
    current_lang = 'bengali'
    is_polite_mode = False
    
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

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    try:
                        draw_robotic_hands(frame, hand_landmarks)
                    except Exception:
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # --- PREDICTION LOGIC ---
            raw_prediction = "Nothing"
            if results.multi_hand_landmarks and model is not None:
                try:
                    data_aux = extract_keypoints(results)
                    prediction_result = model.predict([data_aux])[0]
                    
                    if isinstance(prediction_result, str):
                        raw_prediction = "Nothing" if prediction_result.lower() == "bus" else prediction_result
                    else:
                        prediction_index = int(prediction_result)
                        if 0 <= prediction_index < len(CLASSES):
                            raw_prediction = CLASSES[prediction_index]
                except Exception as e:
                    print(f"⚠️ Predict fail: {e}")
                    raw_prediction = "Nothing"

            # --- STABILITY LOGIC ---
            prediction_buffer.append(raw_prediction)
            
            if len(prediction_buffer) == PREDICTION_BUFFER_SIZE:
                if len(set(prediction_buffer)) == 1: 
                    new_pred = prediction_buffer[0]
                    
                    # Lock not strictly needed if only one thread writes, but safer
                    with state_lock:
                        if current_prediction != new_pred:
                            current_prediction = new_pred
                            print(f"👉 [GESTURE] Verified: {current_prediction}")
                            
                            # EMIT UPDATE IMMEDIATELY
                            active_map, _ = get_active_map(current_lang, is_polite_mode)
                            sentence = active_map.get(current_prediction, "")
                            socketio.emit('prediction_update', {
                                'prediction': current_prediction,
                                'sentence': sentence
                            })

            # --- AUDIO TRIGGER LOGIC ---
            current_time = time.time()
            if current_prediction != "Nothing":
                if current_prediction != last_sent_prediction or (current_time - last_audio_time) > AUDIO_COOLDOWN:
                    last_sent_prediction = current_prediction
                    last_audio_time = current_time
                    
                    # Prepare Audio
                    folder_name = f"{current_lang}_polite" if is_polite_mode else current_lang
                    filename = current_prediction.lower().replace(" ", "_")
                    if is_polite_mode:
                        filename += "_polite"
                    
                    relative_path = f"static/audio/{folder_name}/{filename}.mp3"
                    full_path = os.path.join(os.getcwd(), relative_path)
                    url = "/" + relative_path
                    
                    if os.path.exists(full_path):
                        socketio.emit('play_audio', {'audio_url': url})
                    else:
                        # Generate in BACKGROUND to not block video
                        active_map, lang_code = get_active_map(current_lang, is_polite_mode)
                        text = active_map.get(current_prediction, "")
                        threading.Thread(target=generate_audio_background, args=(text, lang_code, full_path, url)).start()
            else:
                last_sent_prediction = "Nothing"

            # Heartbeat Log
            if (time.time() - last_heartbeat_time) > 20:
                print(f"💓 [HEARTBEAT] System Active - Last Prediction: {current_prediction}")
                last_heartbeat_time = time.time()
                
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect():
    sid = request.sid
    user_sessions[sid] = {
        'lang': 'bengali',
        'polite': False,
        'buffer': collections.deque(maxlen=PREDICTION_BUFFER_SIZE),
        'current_prediction': "Nothing",
        'last_sent_prediction': "Nothing",
        'last_audio_time': 0
    }
    print(f"🔌 Client Connected: {sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in user_sessions:
        del user_sessions[sid]
    print(f"🔌 Client Disconnected: {sid}")

@socketio.on('update_settings')
def handle_settings(data):
    sid = request.sid
    if sid in user_sessions:
        user_sessions[sid]['lang'] = data.get('lang', 'bengali')
        user_sessions[sid]['polite'] = data.get('polite', False)
        print(f"⚙️ Settings Updated for {sid}: {user_sessions[sid]['lang']}, Polite: {user_sessions[sid]['polite']}")

# Create a global hands model configured for rapid websocket queries
socket_hands = mp_hands.Hands(
    static_image_mode=True,
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=2
)
mp_lock = threading.Lock()

@socketio.on('video_frame')
def handle_video_frame(data):
    sid = request.sid
    if sid not in user_sessions:
        return
    session = user_sessions[sid]
    current_lang = session['lang']
    is_polite_mode = session['polite']
    try:
        if ',' in data:
            data = data.split(',')[1]
        
        image_data = base64.b64decode(data)
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        with mp_lock:
            results = socket_hands.process(frame_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                try:
                    draw_robotic_hands(frame, hand_landmarks)
                except Exception:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
        raw_prediction = "Nothing"
        if results.multi_hand_landmarks and model is not None:
            try:
                data_aux = extract_keypoints(results)
                prediction_result = model.predict([data_aux])[0]
                
                if isinstance(prediction_result, str):
                    raw_prediction = "Nothing" if prediction_result.lower() == "bus" else prediction_result
                else:
                    prediction_index = int(prediction_result)
                    if 0 <= prediction_index < len(CLASSES):
                        raw_prediction = CLASSES[prediction_index]
            except Exception as e:
                print(f"⚠️ Predict fail: {e}")
                raw_prediction = "Nothing"
                
        session['buffer'].append(raw_prediction)
        
        if len(session['buffer']) == PREDICTION_BUFFER_SIZE:
            if len(set(session['buffer'])) == 1: 
                new_pred = session['buffer'][0]
                with state_lock:
                    if session['current_prediction'] != new_pred:
                        session['current_prediction'] = new_pred
                        active_map, _ = get_active_map(current_lang, is_polite_mode)
                        sentence = active_map.get(session['current_prediction'], "")
                        emit('prediction_update', {
                            'prediction': session['current_prediction'],
                            'sentence': sentence
                        })
                        
        current_time = time.time()
        if session['current_prediction'] != "Nothing":
            if session['current_prediction'] != session['last_sent_prediction'] or (current_time - session['last_audio_time']) > AUDIO_COOLDOWN:
                session['last_sent_prediction'] = session['current_prediction']
                session['last_audio_time'] = current_time
                
                folder_name = f"{current_lang}_polite" if is_polite_mode else current_lang
                filename = session['current_prediction'].lower().replace(" ", "_")
                if is_polite_mode:
                    filename += "_polite"
                
                relative_path = f"static/audio/{folder_name}/{filename}.mp3"
                full_path = os.path.join(os.getcwd(), relative_path)
                url = "/" + relative_path
                
                if os.path.exists(full_path):
                    emit('play_audio', {'audio_url': url})
                else:
                    active_map, lang_code = get_active_map(current_lang, is_polite_mode)
                    text = active_map.get(session['current_prediction'], "")
                    threading.Thread(target=generate_audio_background, args=(text, lang_code, full_path, url)).start()
        else:
            session['last_sent_prediction'] = "Nothing"
            
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50]) 
        frame_bytes = base64.b64encode(buffer).decode('utf-8')
        emit('processed_frame', 'data:image/jpeg;base64,' + frame_bytes)
        
    except Exception as e:
        print(f"Error processing socket frame: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/log_event')
def log_event():
    msg = request.args.get('msg', 'Unknown')
    print(f"👆 [LOG] {msg}")
    return jsonify({"status": "logged"})

if __name__ == '__main__':
    # Use socketio.run instead of app.run
    socketio.run(app, debug=False)
