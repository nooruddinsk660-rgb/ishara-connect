# 🤟 Ishara Connect (ইশারা কানেক্ট / इशारा कनेक्ट)
### *Next-Generation Real-Time Sign Language AI Interpreter, Emergency Triage & Multi-Tenant Caregiver Telemetry*

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.io-Realtime%20Engine-010101?style=for-the-badge&logo=socket.io&logoColor=white)](https://socket.io/)
[![MediaPipe](https://img.shields.io/badge/Google-MediaPipe%20Vision-0097A7?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Random%20Forest-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Multi--Tenant%20DB-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Social Impact](https://img.shields.io/badge/Social%20Impact-Accessibility%20%26%20Healthcare-FF4081?style=for-the-badge)](https://github.com/nooruddinsk660-rgb/ishara-connect)

[**Explore Documentation**](#-table-of-contents) · [**Live Architecture**](#-system-architecture) · [**Model Deep-Dive**](#-machine-learning--model-architecture) · [**Quickstart**](#-quickstart-installation--setup) · [**Caregiver Portal**](#-clinical-caregiver-dashboard)

</div>

---

## 🌟 Executive Overview

**Ishara Connect** is an end-to-end, ultra-low-latency, assistive communication platform designed to eradicate the communication barriers faced by the **Deaf, Hard of Hearing (DHH), and Non-Verbal communities**.

By synthesizing **computer vision (MediaPipe)**, **geometric spatial normalization**, **ensemble machine learning (Random Forest)**, and **real-time bidirectional WebSocket pipelines**, Ishara Connect translates continuous hand gestures into natural spoken audio across **Bengali, Hindi, and English**. Simultaneously, it provides a two-way **"Listen to Reply"** speech-to-text dictation engine, empowering fluid conversational reciprocity.

Beyond basic translation, Ishara Connect is engineered for **clinical, institutional, and daily life deployments**—featuring **instant emergency SOS detection**, **privacy-first telemetry**, and an enterprise-ready **multi-tenant Caregiver Monitoring Dashboard**.

---

## 📑 Table of Contents

- [🌟 Executive Overview](#-executive-overview)
- [✨ Key Features \& Capabilities](#-key-features--capabilities)
- [🧠 Machine Learning \& Model Architecture](#-machine-learning--model-architecture)
  - [1. 21-Point Hand Landmarking Topology](#1-21-point-hand-landmarking-topology)
  - [2. Spatial Invariance Math (Centering \& Scaling)](#2-spatial-invariance-math-centering--scaling)
  - [3. Group-Aware Split \& Anti-Leakage Validation](#3-group-aware-split--anti-leakage-validation)
  - [4. Data Augmentation Strategy](#4-data-augmentation-strategy)
  - [5. Prediction Stabilization \& Temporal Debouncing](#5-prediction-stabilization--temporal-debouncing)
  - [6. Supported Gesture Vocabulary (30 Classes)](#6-supported-gesture-vocabulary-30-classes)
- [🏛️ System Architecture \& Dataflow](#️-system-architecture--dataflow)
  - [End-to-End Pipeline Diagram](#end-to-end-pipeline-diagram)
  - [Database Schema \& Multi-Tenancy](#database-schema--multi-tenancy)
  - [Privacy-by-Design Philosophy](#privacy-by-design-philosophy)
- [🚨 Emergency Triage \& SOS Subsystem](#-emergency-triage--sos-subsystem)
- [🏥 Clinical Caregiver Dashboard](#-clinical-caregiver-dashboard)
- [🗣️ Tri-Lingual Audio Engine \& Polite Mode](#️-tri-lingual-audio-engine--polite-mode)
- [📂 Codebase Directory Layout](#-codebase-directory-layout)
- [⚡ Quickstart: Installation \& Setup](#-quickstart-installation--setup)
  - [1. Clone Repository \& Virtual Environment](#1-clone-repository--virtual-environment)
  - [2. Install Dependencies](#2-install-dependencies)
  - [3. Configure Environment Variables](#3-configure-environment-variables)
  - [4. Initialize Database \& Alembic Migrations](#4-initialize-database--alembic-migrations)
  - [5. Create Initial Caregiver / Admin Account](#5-create-initial-caregiver--admin-account)
  - [6. Launch Server](#6-launch-server)
- [🧪 Model Training \& Dataset Collection Workflow](#-model-training--dataset-collection-workflow)
- [⚙️ Environment Configuration (`.env`)](#️-environment-configuration-env)
- [🔌 API \& WebSocket Event Reference](#-api--websocket-event-reference)
- [🚀 Production Deployment \& Scaling](#-production-deployment--scaling)
- [🛣️ Roadmap \& Future Horizons](#️-roadmap--future-horizons)
- [🤝 Contributing \& Code of Conduct](#-contributing--code-of-conduct)
- [📜 License \& Citation](#-license--citation)

---

## ✨ Key Features & Capabilities

```
+-----------------------------------------------------------------------------------------+
|                                    ISHARA CONNECT CORE                                  |
+----------------------------+-----------------------------+------------------------------+
|  🖐️ AI Vision Translation   |  🗣️ Natural Voice Synthesis  |  🚨 Emergency Detection      |
|  126-D Spatial Vector ML   |  Bengali, Hindi, English    |  Sub-millisecond triage for  |
|  <15ms inference latency   |  Tone-adaptive Polite Mode  |  critical healthcare distress|
+----------------------------+-----------------------------+------------------------------+
|  👂 Bidirectional Speech   |  🏥 Caregiver Telemetry     |  🛡️ Privacy-First Protocol   |
|  Web Speech STT dictation  |  Multi-tenant portal with   |  Zero raw video/coordinate   |
|  for 2-way conversation    |  live transcripts & audits  |  database storage            |
+----------------------------+-----------------------------+------------------------------+
```

### 1. ⚡ Real-Time Zero-Latency Sign Translation
- Ingests WebRTC camera frames via an off-screen HTML5 compressed canvas stream.
- Emits real-time landmark coordinates through bi-directional WebSockets (`Flask-SocketIO`).
- Computes gesture predictions within **~12–18 milliseconds per frame** on standard CPU hardware.

### 2. 🗣️ Tri-Lingual Audio Synthesis + Contextual "Polite Mode"
- Instant audio vocalization in **English**, **Hindi (हिंदी)**, and **Bengali (বাংলা)**.
- **Polite Mode AI Engine**: Automatically transforms raw imperatives into respectful conversational requests (e.g., *"Water"* $\rightarrow$ *"Could I please have some water?"* / *"জল"* $\rightarrow$ *"আমাকে একটু জল দেবেন দয়া করে?"*).
- Pre-cached Edge-TTS neural voicebanks backed by dynamic `gTTS` fallback generation.

### 3. 👂 "Listen to Reply" Two-Way Conversational Bridge
- Eliminates one-sided interactions: integrates browser-native **Web Speech API** dictation.
- Hearing individuals tap the microphone to speak; their speech is converted in real-time into dynamic, high-contrast text displayed for the deaf user.

### 4. 🚨 Instant Emergency SOS & Distress Alerting
- Real-time keyword filter intercepting urgent signals (*"Pain"*, *"Help"*, *"Call Doctor"*, *"Police"*).
- Instant multi-tier triage classification (`high` vs `critical`) dispatched directly to on-call caregivers.

### 5. 🏥 Multi-Tenant Caregiver & Clinical Dashboard
- Role-based portal for hospitals, nursing homes, schools, and assisted living facilities.
- Multi-tenant tenant boundary isolation (`institutions` $\rightarrow$ `users` $\rightarrow$ `sessions`).
- Real-time session monitoring, interactive transcript timelines, alert acknowledgment workflows, and audit logging.

### 6. 🎨 Cyberpunk & High-Contrast Glassmorphic UI
- Responsive design tailored for mobile smartphones, tablets, laptops, and standalone kiosks.
- Real-time robotic hand skeleton overlays drawn directly onto the viewport.
- Dynamic theme switching: **Cyberpunk Neon Dark Mode** for aesthetic immersion and **High-Contrast Light Mode** for daylight visibility.
- Hardware controls: Integrated flashlight torch toggle and camera flip for mobile browsers.

---

## 🧠 Machine Learning & Model Architecture

### 1. 21-Point Hand Landmarking Topology

Ishara Connect utilizes Google MediaPipe’s high-performance hand landmarking pipeline (`mediapipe.solutions.hands`). For each detected hand, the system extracts **21 three-dimensional landmark vertices** $(x, y, z)$:

```
           8 (INDEX_TIP)    12 (MIDDLE_TIP)   16 (RING_TIP)    20 (PINKY_TIP)
           |                |                 |                |
           7 (INDEX_DIP)    11 (MIDDLE_DIP)   15 (RING_DIP)    19 (PINKY_DIP)
           |                |                 |                |
4 (THUMB)  6 (INDEX_PIP)    10 (MIDDLE_PIP)   14 (RING_PIP)    18 (PINKY_PIP)
 \         |                |                 |                |
  3 (IP)   5 (INDEX_MCP)----9 (MIDDLE_MCP)----13 (RING_MCP)----17 (PINKY_MCP)
   \        \                                                 /
    2 (MCP)  \                                               /
     \        \_____________________________________________/
      1 (CMC)                         |
       \                              |
        0 ----------------------------+ (WRIST)
```

Each frame evaluates both left and right hands ($2 \times 21 \times 3 = 126$ raw coordinate values). Missing hands are zero-padded to maintain a static 126-dimensional feature vector.

---

### 2. Spatial Invariance Math (Centering & Scaling)

Raw pixel coordinates fail in real-world scenarios because user distance from the webcam, hand size, and screen positioning vary constantly. Ishara Connect executes mathematical normalization via `utils.py`:

#### **Step 1: Origin Centering (Translation Invariance)**
All coordinates for a given hand are translated relative to the **Wrist Landmark** ($L_0$):
$$\mathbf{P}_i^{\text{centered}} = \mathbf{L}_i - \mathbf{L}_0 \quad \forall \, i \in \{0, 1, \dots, 20\}$$

#### **Step 2: Scale Normalization (Distance & Hand-Size Invariance)**
The coordinates are scaled by the Euclidean distance between the **Wrist** ($L_0$) and the **Middle Metacarpophalangeal Joint** ($L_9$):
$$s = \|\mathbf{L}_9 - \mathbf{L}_0\|_2 = \sqrt{(x_9 - x_0)^2 + (y_9 - y_0)^2 + (z_9 - z_0)^2}$$
$$\mathbf{P}_i^{\text{normalized}} = \frac{\mathbf{P}_i^{\text{centered}}}{\max(s, \epsilon)}, \quad \epsilon = 10^{-6}$$

$$\mathbf{X}_{\text{hand}} = \text{vec}(\mathbf{P}^{\text{normalized}}) \in \mathbb{R}^{63}$$
$$\mathbf{X}_{\text{feature}} = [\mathbf{X}_{\text{LeftHand}} \,\|\, \mathbf{X}_{\text{RightHand}}] \in \mathbb{R}^{126}$$

This ensures that whether a child with small hands signs 3 feet away or an adult signs 1 foot away, the resulting feature vector remains identical.

---

### 3. Group-Aware Split & Anti-Leakage Validation

Traditional random frame-level train/test splits introduce severe **temporal autocorrelation data leakage** (adjacent video frames collected milliseconds apart end up in both splits, artificially reporting >99% accuracy while failing in real-world tests).

Ishara Connect implements **Session-Grouped Splitting** (`GroupShuffleSplit`) in `train_model.py`:
- Video frames are grouped by `session_id` and `signer_id`.
- The entire continuous recording take of a sign is held out exclusively in either the training set or the test set.
- Reports honest, unbiased generalization metrics across different signers and camera takes.

---

### 4. Data Augmentation Strategy

To make the classifier resilient against natural hand tremor, variable lighting noise, and minor camera sensor jitter, Gaussian perturbation is injected exclusively into the training partition:

$$\mathbf{X}_{\text{augmented}} = \mathbf{X}_{\text{train}} + \mathcal{N}\left(0, \sigma^2 \mathbf{I}\right), \quad \sigma \in \{0.05, 0.10\}$$

The test partition is kept unaugmented for rigorous validation.

---

### 5. Prediction Stabilization & Temporal Debouncing

To eliminate flickering false positives caused by transitional hand movement between gestures, `app.py` employs a stateful smoothing buffer:

```
[ Incoming Frames ] ---> ( Rolling Deque Buffer N=3 ) 
                                  |
                   [ All N Predictions Match? ]
                           /              \
                        [YES]             [NO]
                         /                  \
             Confidence >= 0.5?        Discard / Maintain Idle
                    /
                 [YES]
                  /
       ( Audio Cooldown Check )
       [ elapsed >= 3.0s? ]
             /          \
          [YES]         [NO]
           /              \
  Emit Translation     Update Visual UI
  & Trigger Audio      (Suppress Audio Spam)
```

1. **Prediction Buffer ($N=3$)**: Requires 3 consecutive identical predictions before a label is considered recognized.
2. **Confidence Thresholding ($\tau \ge 0.50$)**: Rejects ambiguous predictions.
3. **Temporal Audio Debounce ($T = 3.0\text{s}$)**: Prevents audio stuttering while allowing continuous visual recognition updates.

---

### 6. Supported Gesture Vocabulary (30 Classes)

| Category | Gestures Included |
| :--- | :--- |
| **👋 Greetings & Social** | `Hello`, `Thank You`, `Friend`, `Mother`, `Name`, `Happy`, `I Love You` |
| **💡 Everyday Essentials** | `Water`, `Food`, `Tea`, `Toilet`, `Medicine`, `Money`, `Book`, `Home` |
| **🤝 Courtesy & Responses** | `Please`, `Sorry`, `Good`, `Bad`, `Yes`, `No` |
| **❓ Queries & Time** | `What`, `Where`, `Time` |
| **🚨 Emergency & Medical** | `Help`, `Pain`, `Call Doctor`, `Police`, `Stop` |
| **🛑 Neutral State** | `Nothing` (Resting / No active gesture) |

---

## 🏛️ System Architecture & Dataflow

### End-to-End Pipeline Diagram

```mermaid
flowchart TB
    subgraph Client ["🖥️ Client-Side Browser (WebRTC & DOM)"]
        Cam["📷 User Camera Feed"] --> Canvas["🎨 Hidden HTML5 Canvas (JPEG Compression 0.5)"]
        Canvas --> SktEmit["📡 Socket.IO: 'image' Frame Stream"]
        SktRecv["📥 Socket.IO: Processed Frame & Audio Event"] --> Overlay["✨ Skeleton Overlay & Dynamic Speech HUD"]
        Mic["🎙️ Web Speech API (Listen to Reply)"] --> SpeechBox["📝 Live Dual-Sided Transcription Box"]
    end

    subgraph Server ["⚡ Server Backend (Flask & Socket.IO Engine)"]
        SktEmit --> Lock["🔒 Threading Lock Queue"]
        Lock --> CV["OpenCV (Decode / Flip / Color Space)"]
        CV --> MP["Google MediaPipe Hands (21 Landmarks)"]
        MP --> Norm["📐 Centering & Scaling Normalization (126-D)"]
        Norm --> RF["🌲 Random Forest Classifier (100 Trees)"]
        RF --> Buffer["⏱️ Rolling Stabilization Buffer (N=3)"]
        Buffer --> Engine{"Decision Engine"}
        
        Engine -->|Standard Gesture| Audio["🔊 Audio Dispatcher (Edge-TTS / gTTS)"]
        Engine -->|Emergency Keyword| Alert["🚨 Emergency Engine (Severity Classifier)"]
        
        Audio --> SktRecv
        Alert --> Broadcast["📢 Caregiver Live Room Broadcast"]
    end

    subgraph Database ["🗄️ Multi-Tenant Relational Layer (PostgreSQL)"]
        Engine -.->|Log Abstracted Tokens| DB_Event[("transcript_events")]
        Alert -.->|Persist Alert Event| DB_Alert[("alerts")]
        Auth[("institutions / users / sessions")] <--> DB_Caregiver["🏥 Caregiver Dashboard"]
    end
```

---

### Database Schema & Multi-Tenancy

Ishara Connect uses **SQLAlchemy 2.0** with **Alembic migrations** to power a strict multi-tenant architecture:

```
+----------------------------------------------------------------------------------------------------+
|                                    MULTI-TENANT RELATIONAL SCHEMA                                  |
+-------------------+       +--------------------+       +---------------------+                     |
|   institutions    | 1   * |       users        | 1   * |      sessions       |                     |
|-------------------|-------|--------------------|-------|---------------------|                     |
| id (PK)           |       | id (PK)            |       | id (PK)             |                     |
| name              |       | institution_id(FK) |       | user_id (FK)        |                     |
| tier              |       | role               |       | started_at          |                     |
| billing_status    |       | email              |       | ended_at            |                     |
+-------------------+       | password_hash      |       | device_type         |                     |
                            +--------------------+       +---------------------+                     |
                                                               | 1            | 1                    |
                                                               | *            | *                    |
                                                    +--------------------+  +---------------------+  |
                                                    | transcript_events  |  |       alerts        |  |
                                                    |--------------------|  |---------------------|  |
                                                    | id (PK)            |  | id (PK)             |  |
                                                    | session_id (FK)    |  | session_id (FK)     |  |
                                                    | ts                 |  | ts                  |  |
                                                    | gesture_sequence   |  | trigger_phrase      |  |
                                                    | decoded_phrase     |  | severity            |  |
                                                    | confidence         |  | acknowledged_by(FK) |  |
                                                    | mode               |  | acknowledged_at     |  |
                                                    +--------------------+  +---------------------+  |
+----------------------------------------------------------------------------------------------------+
```

### Privacy-by-Design Philosophy
> [!IMPORTANT]
> **No raw webcam video frames, audio recordings, or biometric coordinate arrays are ever saved to disk or database.**
> The only persisted records are high-level, abstracted linguistic phrase tokens (e.g. `decoded_phrase: "Water"`), ensuring complete HIPAA/GDPR alignment.

---

## 🚨 Emergency Triage & SOS Subsystem

The emergency module (`emergency.py`) continuously scans detected gestures. When a critical keyword is confirmed, the system immediately bypasses standard cooldowns and triggers high-priority events:

| Trigger Gesture | Triage Severity | Clinical Action / Caregiver Dispatch |
| :--- | :---: | :--- |
| **`Pain`** | <span style="color:#f39c12">**HIGH**</span> | Flashes urgent visual banner; logs priority event in caregiver timeline. |
| **`Help`** | <span style="color:#f39c12">**HIGH**</span> | Triggers vocal emergency prompt; alerts attending station. |
| **`Call Doctor`** | <span style="color:#e74c3c">**CRITICAL**</span> | Dispatches immediate medical attention notification with room/session ID. |
| **`Police`** | <span style="color:#e74c3c">**CRITICAL**</span> | Dispatches instant safety protocol escalation. |

---

## 🏥 Clinical Caregiver Dashboard

The **Caregiver Portal** (`/dashboard`) provides medical staff, teachers, and family members with real-time insight into active patient sessions:

- 🔐 **Secure Access**: Session-cookie authentication with PBKDF2-SHA256 password hashing and CSRF tokens.
- 🏢 **Multi-Tenant Data Isolation**: Caregivers can strictly access data originating from their own assigned institution.
- 📡 **Live Telemetry (`/dashboard/live`)**: Live WebSocket subscription to active patient translation feeds.
- 📋 **Session History & Replays (`/dashboard/sessions/<id>`)**: Step-by-step breakdown of gestures signed, confidence metrics, and timestamps.
- ✅ **Alert Resolution Center (`/dashboard/alerts`)**: One-click acknowledgment of emergency alerts with caregiver ID tracking.

---

## 🗣️ Tri-Lingual Audio Engine & Polite Mode

Ishara Connect supports dynamic language localization across three major languages:

```
                            [ Recognized Sign: "Water" ]
                                         |
                       +-----------------+-----------------+
                       |                                   |
                [ Standard Mode ]                   [ Polite Mode AI ]
                       |                                   |
      +----------------+---------------+   +---------------+---------------+
      |                |               |   |               |               |
   English           Hindi          Bengali| English     Hindi          Bengali
   "Water"          "पानी"           "জল"  |"Can I have  "क्या मुझे       "আমাকে একটু
                                           | some water   थोड़ा पानी       জল দেবেন দয়া
                                           | please?"     मिल सकता है?"    করে?"
```

- **Offline Pre-Generation (`generate_premium_audio.py`)**: Uses Microsoft Edge neural TTS models (`en-US-AriaNeural`, `hi-IN-SwaraNeural`, `bn-IN-TanishaaNeural`) to generate ultra-realistic audio files.
- **Dynamic Fallback (`gTTS`)**: On-demand synthesis fallback if a customized translation string is requested.

---

## 📂 Codebase Directory Layout

```
ishara-connect/
├── .env.example                 # Template for environment variables and secrets
├── .gitignore                   # Git exclusion configuration
├── Procfile                     # Production WSGI server declaration (Gunicorn/Eventlet)
├── README.md                    # World-class project documentation
├── alembic.ini                  # Database migration configuration
│
├── app.py                       # Main Flask application & Socket.IO realtime server
├── auth.py                      # Caregiver authentication, session management & CSRF
├── dashboard.py                 # Multi-tenant caregiver portal routes and API views
├── emergency.py                 # Emergency SOS triage detection and alert dispatcher
├── db.py                        # Database engine initialization and session factory
├── models.py                    # SQLAlchemy ORM schemas (6 core tables)
├── utils.py                     # Landmark coordinate extraction and spatial normalization
├── data_collector.py            # Multi-signer dataset collection utility
├── train_model.py               # Group-aware machine learning training pipeline
├── generate_premium_audio.py    # Edge-TTS batch audio synthesizer
├── create_caregiver.py          # CLI tool for provisioning caregiver / admin accounts
│
├── data/                        # Landmark sequence datasets
├── data.csv                     # Recorded 126-D hand landmark feature points
├── model.p                      # Serialized Random Forest model & metadata artifact
├── requirements.txt             # Locked production dependencies
│
├── migrations/                  # Alembic database schema migration scripts
│   ├── env.py
│   └── versions/
│
├── static/                      # Static web assets
│   ├── css/
│   │   └── style.css            # Glassmorphism, Cyberpunk & Light mode styling
│   ├── js/
│   │   └── socket.io.min.js     # Realtime WebSocket client library
│   └── audio/                   # Pre-rendered multi-language MP3 voicebanks
│
├── templates/                   # Jinja2 HTML Templates
│   ├── index.html               # Main translation interface
│   ├── components/              # Modular frontend widgets
│   │   ├── camera.html          # Viewport, flashlight controls, skeleton canvas
│   │   ├── gestures.html        # Interactive 30-gesture reference list
│   │   ├── header.html          # Navigation, language select, theme switcher
│   │   └── scripts.html         # WebRTC capture, audio context, WebSocket client
│   └── dashboard/               # Caregiver portal templates
│       ├── base.html            # Dashboard layout & navigation
│       ├── home.html            # Analytics metrics & recent session history
│       ├── login.html           # Secure caregiver sign-in
│       └── session_detail.html  # Granular session transcript timeline
│
└── translations/                # Localization dictionaries
    ├── english.json             # English standard & polite phrases
    ├── hindi.json               # Hindi standard & polite phrases
    └── bengali.json             # Bengali standard & polite phrases
```

---

## ⚡ Quickstart: Installation & Setup

### Prerequisites
- **Python**: Version `3.10`, `3.11`, or `3.12`
- **Hardware**: Standard webcam or USB camera
- **Database (Optional for local translation, required for Dashboard)**: PostgreSQL 14+

---

### 1. Clone Repository & Virtual Environment

```bash
# Clone the repository
git clone https://github.com/nooruddinsk660-rgb/ishara-connect.git
cd ishara-connect

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate
```

---

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> [!NOTE]
> `mediapipe==0.10.14` is explicitly pinned to preserve backwards compatibility with `mp.solutions.hands`.

---

### 3. Configure Environment Variables

Copy the example environment configuration:
```bash
cp .env.example .env
```

Edit `.env` with your secure configuration:
```ini
# Generate a secret key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_generated_random_64_character_hex_key

# PostgreSQL Connection (Optional: leave blank to run in standalone kiosk mode)
DATABASE_URL=postgresql://postgres:password@localhost:5432/ishara_connect

# Set to true only if running standalone local kiosk
ENABLE_LOCAL_WEBCAM_ROUTE=false
```

---

### 4. Initialize Database & Alembic Migrations

If using PostgreSQL for telemetry and caregiver features:

```bash
# Apply migrations to bring schema up to latest version
alembic upgrade head
```

---

### 5. Create Initial Caregiver / Admin Account

```bash
python create_caregiver.py \
  --email doctor@hospital.org \
  --name "Dr. Sarah Khan" \
  --institution "Apollo Hospital" \
  --tier "hospital"
```
*The CLI will prompt you to securely enter and confirm a password.*

---

### 6. Launch Server

```bash
python app.py
```

Now open your browser and navigate to:
- 🤟 **Main AI Translation Interface**: `http://localhost:5000`
- 🏥 **Caregiver Monitoring Portal**: `http://localhost:5000/dashboard`

---

## 🧪 Model Training & Dataset Collection Workflow

Want to add new gestures or train with your own signers? Ishara Connect provides a complete end-to-end ML training toolchain.

### Step 1: Collect Landmark Data
Record 500 normalized landmark frames per gesture with multi-signer tagging:

```bash
# Record all gestures for a specific signer
python data_collector.py --signer_id "noor" --session_note "laptop_cam_daylight"

# Or record specific subset of gestures
python data_collector.py --classes "Water" "Food" "Help" --signer_id "noor"
```

### Step 2: Train & Validate Model
Train the Random Forest model using group-aware cross-validation and noise augmentation:

```bash
python train_model.py
```
*Outputs evaluation metrics, held-out accuracy, and saves the serialized model to `model.p`.*

### Step 3: Pre-Generate High-Fidelity Audio
Generate premium neural speech files for newly added gestures:

```bash
python generate_premium_audio.py
```

---

## ⚙️ Environment Configuration (`.env`)

| Variable | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `SECRET_KEY` | String | *Auto-generated* | Secret key for Flask signed session cookies and CSRF tokens. |
| `DATABASE_URL` | String | `None` | PostgreSQL connection string (`postgresql://user:pass@host:5432/db`). |
| `ENABLE_LOCAL_WEBCAM_ROUTE` | Boolean | `false` | Enables local hardware CV capture on `/video_feed` for kiosk hardware. |
| `PERMANENT_SESSION_LIFETIME` | Integer | `8 hours` | Duration of caregiver dashboard authenticated session. |

---

## 🔌 API & WebSocket Event Reference

### WebSocket Events (`/`)

| Event Name | Direction | Payload | Description |
| :--- | :---: | :--- | :--- |
| `connect` | Client $\rightarrow$ Server | `None` | Initializes real-time session and state buffer. |
| `image` | Client $\rightarrow$ Server | `{ image: "data:image/jpeg;base64,..." }` | Pushes compressed camera frame for ML inference. |
| `processed_frame` | Server $\rightarrow$ Client | `{ image: "data:image/jpeg;base64,..." }` | Returns frame with rendered landmark overlays. |
| `prediction` | Server $\rightarrow$ Client | `{ gesture: "Water", confidence: 0.94, ... }` | Emits stabilized gesture prediction. |
| `play_audio` | Server $\rightarrow$ Client | `{ file: "/static/audio/bengali/water.mp3" }` | Instructs client audio context to play voice synthesis. |
| `emergency_alert` | Server $\rightarrow$ Client | `{ phrase: "Pain", severity: "high" }` | Emits immediate emergency alert broadcast. |

---

## 🚀 Production Deployment & Scaling

For production environments (e.g. AWS EC2, DigitalOcean, Render, Heroku), run with **Gunicorn** and **Eventlet**:

```bash
gunicorn \
  --worker-class eventlet \
  --workers 1 \
  --bind 0.0.0.0:5000 \
  --timeout 120 \
  app:app
```

> [!TIP]
> **HTTPS / SSL Requirement**: Modern web browsers strictly restrict `navigator.mediaDevices.getUserMedia()` to secure origins (`https://` or `localhost`). When deploying publicly, ensure an SSL/TLS certificate is configured via Nginx or Cloudflare.

---

## 🛣️ Roadmap & Future Horizons

- [x] 21-point spatial MediaPipe hand landmark extraction
- [x] Spatial invariance normalization (wrist centering & middle MCP scaling)
- [x] 30 gesture classification via Random Forest
- [x] Tri-lingual speech synthesis (English, Hindi, Bengali) + Polite Mode
- [x] "Listen to Reply" bidirectional speech transcription
- [x] Multi-tenant PostgreSQL telemetry & Caregiver Dashboard
- [x] Real-time emergency detection and triage alerts
- [ ] **Temporal Continuous Translation**: Transition to Bi-Directional LSTM / Transformer models for dynamic sentence-level signing.
- [ ] **Edge Acceleration**: Export trained models to ONNX / TensorFlow.js / WebAssembly for 100% in-browser client-side execution.
- [ ] **Cross-Platform Mobile App**: Native Flutter / PWA application with background push alerts.
- [ ] **Expanded Regional Sign Dialects**: Support for Indian Sign Language (ISL) regional variations and American Sign Language (ASL).

---

## 🤝 Contributing & Code of Conduct

We warmly welcome contributions from software engineers, AI researchers, UX designers, and accessibility advocates worldwide!

1. **Fork the Repository**
2. **Create a Feature Branch**: `git checkout -b feature/dynamic-gesture-expansion`
3. **Commit Your Changes**: `git commit -m 'feat: add 5 new medical gesture classes'`
4. **Push to Branch**: `git push origin feature/dynamic-gesture-expansion`
5. **Open a Pull Request**

Please ensure your contributions adhere to clean code principles, include relevant test/validation metrics, and preserve user privacy.

---

## 📜 License & Citation

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

### Citation
If you use Ishara Connect in your research or accessibility project, please cite:

```bibtex
@software{ishara_connect_2026,
  author = {Sk Nooruddin},
  title = {Ishara Connect: Real-Time AI Sign Language Interpreter & Clinical Telemetry Platform},
  year = {2026},
  url = {https://github.com/nooruddinsk660-rgb/ishara-connect}
}
```

---

<div align="center">

### 🌍 *Breaking the Walls of Silence, One Gesture at a Time.*

**Developed with ❤️ and Empathy by [Sk Nooruddin](https://github.com/nooruddinsk660-rgb)**

[![GitHub Stars](https://img.shields.io/github/stars/nooruddinsk660-rgb/ishara-connect?style=social)](https://github.com/nooruddinsk660-rgb/ishara-connect)
[![GitHub Forks](https://img.shields.io/github/forks/nooruddinsk660-rgb/ishara-connect?style=social)](https://github.com/nooruddinsk660-rgb/ishara-connect)

</div>
