import base64
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
from dotenv import load_dotenv
load_dotenv()  # no-op if .env doesn't exist (e.g. on a platform that injects env vars directly)

from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import emit
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
import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from utils import extract_keypoints
from db import DB_ENABLED, SessionLocal, init_db, get_or_create_default_patient_user
from models import Session as DBSession, TranscriptEvent, utcnow
from emergency import check_emergency, create_alert
from avatar_replies import get_avatar_replies

# Add local site_packages to path
sys.path.append(os.path.join(os.getcwd(), "site_packages"))

# Robust import for gTTS
try:
    from gtts import gTTS
except ImportError:
    try:
        from gtts import gTTS
    except ImportError:
        pass

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32))
# Stage 2: the dashboard uses real signed-cookie login sessions, so unlike
# Phase 0 (where nothing depended on SECRET_KEY staying stable), a restart
# with no SECRET_KEY set now logs every caregiver out. Set it in .env for
# any deployment that isn't purely local/throwaway.
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=8)  # one shift

from extensions import socketio
socketio.init_app(app, cors_allowed_origins="*")

from dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

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

# --- STAGE 1: POSTGRES TRANSCRIPT LOGGING (optional, additive) ---
init_db()

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
def generate_audio_background(sid, text, lang_code, full_path, url):
    """Generate audio in a separate thread and emit event when done.

    sid=None only from the local-kiosk-mode gen_frames() route (no per-client
    concept there -- see app.py's ENABLE_LOCAL_WEBCAM_ROUTE), where
    broadcasting is correct since there's just one physical screen watching.
    Every other caller should pass a real sid: without it, socketio.emit()
    with no room broadcasts to every connected client, which means anyone
    else with the page open would hear this audio too."""
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(full_path)
        print(f"✅ [BG] Audio Generated: {full_path}")
        if sid:
            socketio.emit('play_audio', {'audio_url': url}, to=sid, namespace='/')
        else:
            socketio.emit('play_audio', {'audio_url': url})
    except Exception as e:
        print(f"❌ [BG] TTS Error: {e}")

def log_transcript_and_alert_background(sid, institution_id, db_session_id, new_pred, confidence, gesture_buffer):
    """Runs the Postgres writes (and any resulting dashboard/emergency socket
    pushes) in a background thread, off the video pipeline's critical path.

    Before this, every confirmed word stalled processed_frame behind a
    synchronous DB round-trip -- two round trips for an emergency word
    (transcript_event, then alert) -- because the client won't capture its
    next frame until processed_frame arrives (see startFrameStreaming()'s
    isFrameProcessing gate in scripts.html). That's the difference between a
    smooth feed and a visible hitch exactly at the moment a gesture is
    recognized. Mirrors the generate_audio_background() pattern above."""
    if not (DB_ENABLED and db_session_id):
        return
    try:
        event_ts = utcnow()
        db = SessionLocal()
        db.add(TranscriptEvent(
            session_id=db_session_id,
            ts=event_ts,
            gesture_sequence=json.dumps(gesture_buffer),
            decoded_phrase=new_pred,
            confidence=confidence,
            mode='word',
        ))
        db.commit()
        db.close()

        # Stage 2: push this to any caregiver dashboard watching this
        # institution's live feed. Server-picked room -- see dashboard.py's
        # handle_dashboard_join(), a client can never choose this room itself.
        if institution_id:
            socketio.emit('new_transcript_event', {
                'session_id': db_session_id,
                'decoded_phrase': new_pred,
                'confidence': confidence,
                'ts': event_ts.isoformat(),
            }, to=f"institution_{institution_id}", namespace='/dashboard')

        # Stage 3: Emergency Detector. Still fires off the same verified-
        # prediction event, just no longer blocking the frame that carries it.
        severity = check_emergency(new_pred)
        if severity:
            db = SessionLocal()
            alert = create_alert(db, db_session_id, new_pred, severity)
            alert_payload = {
                'id': alert.id,
                'session_id': alert.session_id,
                'trigger_phrase': alert.trigger_phrase,
                'severity': alert.severity,
                'ts': alert.ts.isoformat(),
            }
            db.close()

            if institution_id:
                socketio.emit('emergency_alert', alert_payload,
                              to=f"institution_{institution_id}", namespace='/dashboard')

            # Targets this ONE client via its own auto-joined sid room. Not a
            # bare emit() -- that only works inside a live request context,
            # which a background thread isn't -- and not a bare
            # socketio.emit() with no room either, which would broadcast to
            # every connected client (see generate_audio_background's fix
            # above for the same class of bug).
            socketio.emit('emergency_confirmed', {
                'trigger_phrase': new_pred,
                'severity': severity,
            }, to=sid, namespace='/')
    except Exception as e:
        print(f"⚠️ [DB] Background logging failed: {e}")

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

# LOCAL KIOSK MODE ONLY. This opens a webcam device attached directly to the
# machine running this Flask process (cv2.VideoCapture(0)). It is unrelated to
# the normal browser flow, which streams frames over Socket.IO instead (see
# handle_frame() below) and works from any client. On a cloud host there is no
# camera device 0, so this will just log "Could not open webcam" and return.
# Gated off by default -- see ENABLE_LOCAL_WEBCAM_ROUTE below.
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
                        # gen_frames() has no per-client sid (local kiosk mode,
                        # see the ENABLE_LOCAL_WEBCAM_ROUTE gate) -- sid=None is
                        # correct here, not an oversight.
                        active_map, lang_code = get_active_map(current_lang, is_polite_mode)
                        text = active_map.get(current_prediction, "")
                        threading.Thread(target=generate_audio_background, args=(None, text, lang_code, full_path, url)).start()
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
        'last_audio_time': 0,
        'db_session_id': None,
        'institution_id': None,
    }
    print(f"🔌 Client Connected: {sid}")

    if DB_ENABLED:
        try:
            db = SessionLocal()
            user = get_or_create_default_patient_user(db)
            db_session = DBSession(user_id=user.id, device_type='browser')
            db.add(db_session)
            db.commit()
            user_sessions[sid]['db_session_id'] = db_session.id
            user_sessions[sid]['institution_id'] = user.institution_id
            db.close()
        except Exception as e:
            print(f"⚠️ [DB] Failed to open transcript session: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in user_sessions:
        db_session_id = user_sessions[sid].get('db_session_id')
        if DB_ENABLED and db_session_id:
            try:
                db = SessionLocal()
                db_session = db.get(DBSession, db_session_id)
                if db_session:
                    db_session.ended_at = utcnow()
                    db.commit()
                db.close()
            except Exception as e:
                print(f"⚠️ [DB] Failed to close transcript session: {e}")
        del user_sessions[sid]
    print(f"🔌 Client Disconnected: {sid}")

@socketio.on('update_settings')
def handle_settings(data):
    sid = request.sid
    if sid in user_sessions:
        user_sessions[sid]['lang'] = data.get('lang', 'bengali')
        user_sessions[sid]['polite'] = data.get('polite', False)
        print(f"⚙️ Settings Updated for {sid}: {user_sessions[sid]['lang']}, Polite: {user_sessions[sid]['polite']}")

# Create a global hands model configured for rapid websocket queries (video tracking mode)
socket_hands = mp_hands.Hands(
    static_image_mode=False,
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

                        # Computed once here (not just inside the DB block below) so the
                        # patient-facing UI can show real model confidence live, not just
                        # the caregiver dashboard. new_pred != "Nothing" guarantees data_aux
                        # was set above this call (raw_prediction only equals a real class
                        # when that try block succeeded).
                        confidence = None
                        if new_pred != "Nothing" and hasattr(model, 'predict_proba'):
                            confidence = float(model.predict_proba([data_aux])[0].max())

                        emit('prediction_update', {
                            'prediction': session['current_prediction'],
                            'sentence': sentence,
                            'confidence': confidence,
                        })

                        # --- Stage 1/2/3 logging + dashboard/emergency pushes now run in
                        # the background (see log_transcript_and_alert_background above) so
                        # a Postgres round-trip never stalls processed_frame -- and by
                        # extension, the client's NEXT captured frame too, since it waits
                        # for processed_frame before sending another one.
                        if new_pred != "Nothing":
                            threading.Thread(
                                target=log_transcript_and_alert_background,
                                args=(sid, session.get('institution_id'), session.get('db_session_id'),
                                      new_pred, confidence, list(session['buffer']))
                            ).start()

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
                    threading.Thread(target=generate_audio_background, args=(sid, text, lang_code, full_path, url)).start()
        else:
            session['last_sent_prediction'] = "Nothing"
            
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 45]) 
        frame_bytes = base64.b64encode(buffer).decode('utf-8')
        emit('processed_frame', 'data:image/jpeg;base64,' + frame_bytes)
        
    except Exception as e:
        print(f"Error processing socket frame: {e}")

@app.route('/')
def index():
    return render_template('index.html', avatar_replies=get_avatar_replies())

@app.route('/favicon.ico')
def favicon():
    return ('', 204)


if os.environ.get('ENABLE_LOCAL_WEBCAM_ROUTE', 'false').lower() == 'true':
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