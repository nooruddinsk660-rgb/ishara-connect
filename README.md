# 🤟 Ishara Connect
### *Breaking the Walls of Silence, One Gesture at a Time.*

![Banner](https://img.shields.io/badge/Status-Active-success?style=for-the-badge) ![Version](https://img.shields.io/badge/Version-2.1.0-blue?style=for-the-badge) ![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge) ![Impact](https://img.shields.io/badge/Social%20Impact-High-red?style=for-the-badge)

---

## 🌍 The Mission: Why Ishara?

Imagine a world where you speak, but no one hears you. For millions of people in the Deaf and Mute community, this is a daily reality. Simple interactions—ordering a coffee, asking for help, or chatting with a friend—become hurdles of frustration and isolation.

**Ishara Connect** was born out of a deep empathy for this silence. It is not just an application; it is a **bridge**.

We believe that **communication is a fundamental human right**. By leveraging advanced Artificial Intelligence and Computer Vision, we empower individuals to express themselves freely and be understood instantly. We are not just translating signs; we are translating **human connection**, restoring dignity, and fostering a culture of inclusivity where every voice, silent or spoken, matters.

---

## ✨ What Makes It Special?

Ishara Connect goes beyond simple translation. It mimics the nuance of human interaction.

*   **🗣️ Real-Time Voice Synthesis**: Instantly translates hand gestures into natural, spoken language (Bengali, Hindi, English).
*   **👂 Listen to Reply (Two-Way Communication)**: The app listens to the other person and displays their speech as text, allowing for a full, fluid conversation.
*   **🎩 Polite Mode AI**: Understanding that context matters, our AI can transform a raw gesture like "Water" into a polite request: *"Could I please have some water?"*
*   **🎨 Cyberpunk & Clean Themes**: A stunning, accessible UI that adapts to the user's preference—whether they love the futuristic *Cyberpunk* aesthetic or a high-contrast *Light Mode* for better visibility.

---

## � Key Features

| Feature | Description |
| :--- | :--- |
| **Real-Time Gesture Recognition** | Detects essential hand signs instantly using MediaPipe & Random Forest. |
| **Multi-Language Core** | Seamlessly switches between **English**, **Hindi**, and **Bengali**. |
| **Smart Audio Engine** | Thread-safe, non-blocking TTS generation for smooth playback. |
| **Robotic Hand VFX** | A futuristic tracking overlay that visualizes AI perception in real-time. |
| **Flashlight & Camera** | Integrated hardware controls for low-light environments. |
| **WebSockets** | Zero-latency feedback loop for gestures and audio status. |

---

## 🛠️ Under the Hood (Tech Stack)

We built Ishara Connect with stability and performance in mind.

*   **Core AI**: `OpenCV`, `MediaPipe`, `Scikit-Learn` (Random Forest Classifier).
*   **Backend**: `Python 3.11`, `Flask`, `Flask-SocketIO` (Async Event Handling).
*   **Frontend**: `HTML5`, `CSS3` (Glassmorphism), `JavaScript` (Socket.IO client).
*   **Audio**: `gTTS` (Google Text-to-Speech) with dynamic caching and thread locking.
*   **Deployment**: Ready for cloud deployment with `Gunicorn` and `Eventlet`.

---

## 📂 File Structure & Descriptions

Below is the directory structure of the **Ishara Connect** codebase, along with a detailed explanation of what each file is doing:

```
ishara-connect/
├── data/                    # Landmark sequences data directory
├── static/                  # Frontend static assets
│   ├── css/
│   │   └── style.css        # Main application styling (Cyberpunk & Light modes)
│   ├── js/
│   │   └── socket.io.min.js # Socket.IO client library for real-time communication
│   └── audio/               # Cached/pre-generated Text-to-Speech MP3 audio assets
├── templates/               # Flask Jinja2 HTML templates
│   ├── index.html           # Main entry page template
│   └── components/          # Modular UI components
│       ├── camera.html      # Camera preview card with overlays and controls
│       ├── gestures.html    # Sidebar showing the 30 gesture classes
│       ├── header.html      # Top navigation, language selection, and themes
│       └── scripts.html     # Client-side JavaScript (websockets, webcam, drawing)
├── translations/            # Localization dictionary files
│   ├── bengali.json         # Bengali translation maps (standard & polite)
│   ├── english.json         # English translation maps (standard & polite)
│   └── hindi.json           # Hindi translation maps (standard & polite)
├── .env                     # Local environment configuration secrets
├── .gitignore               # Files and patterns ignored by Git
├── app.py                   # Main Flask & Socket.IO server (handles streaming & inference)
├── data.csv                 # Dataset containing recorded hand landmark keypoints
├── data_collector.py        # Webcam tool to record keypoint dataset for target gestures
├── generate_premium_audio.py# Pre-generator script for edge-tts audio caching
├── Ishara_Connect_Project_Report.md # Full documentation and architecture overview
├── Procfile                 # Deployment configurations for production web server
├── train_model.py           # ML training script to generate the gesture classification model
└── utils.py                 # Keypoint extraction and normalization helper functions
```

### 📋 What Each File is Doing:

*   **`app.py`**: The central application controller. It initializes the Flask app, configures Socket.IO, loads the trained Machine Learning model (`model.p`), and coordinates multi-threaded real-time hand-landmark predictions via WebSockets. It also serves standard HTTP routes and acts as a fallback TTS generator.
*   **`data_collector.py`**: The data collection tool (the dataset creation task file). It captures raw frames from the webcam, detects hand landmarks using MediaPipe, extracts their normalized coordinates, and records them under specific gesture labels into `data.csv`. This script supports recording all 30 classes or target subsets via command-line arguments.
*   **`train_model.py`**: The model trainer. It loads the keypoints from `data.csv`, applies dataset augmentation (injecting Gaussian noise to make predictions robust to hand sizes and distances), trains a `RandomForestClassifier`, and pickles the final model to `model.p` alongside accuracy metrics.
*   **`utils.py`**: The keypoint preprocessing utility. It defines `extract_keypoints()`, which extracts hand landmarks, translates them relative to the wrist coordinates (centering), and scales them relative to the middle MCP distance (normalization) so the classification is invariant to camera distance.
*   **`generate_premium_audio.py`**: An offline asset pre-generator. It connects to the `edge-tts` API to pre-generate high-quality natural voice files for all translation strings in Bengali, Hindi, and English (for both standard and polite modes), saving them locally to avoid dynamic latency during live video translation.
*   **`templates/components/scripts.html`**: The frontend logic driver. Connects to the Flask-SocketIO server, requests/captures webcam frames, pushes them to the backend, parses processed frame canvas data, listens for predicted gesture updates, triggers audio playback, and dynamically updates translations in real-time.
*   **`translations/` JSON files**: Define standard and polite translations for all 30 gesture categories in three distinct languages, mapping the classifier outputs to spoken sentences.

---

## 📸 Screenshots

*(Add your screenshots here to show off the beautiful UI!)*

---

## ⚡ Getting Started

Join us in building a more inclusive world.

### Prerequisites
*   Python 3.10+
*   A working Webcam

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/nooruddinsk660-rgb/ishara-connect.git
    cd ishara-connect
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *If `requirements.txt` is missing, install manually:*
    ```bash
    pip install flask flask-socketio opencv-python mediapipe scikit-learn pandas numpy gtts eventlet
    ```

3.  **Run the Application**
    ```bash
    python app.py
    ```

4.  **Experience It**
    Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 🤝 Contributing to the Cause

We encourage developers, designers, and accessibility advocates to contribute. Whether it's adding new gestures, optimizing the model, or refining the UI for better accessibility—your help creates impact.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License & Acknowledgements

This project is open-source under the **MIT License**.

Special thanks to the open-source community behind MediaPipe and OpenCV for making accessibility technology reachable for everyone.

---

<div align="center">

**Made with ❤️ and Empathy by [Sk Nooruddin]**

*"Technology is best when it brings people together."*

</div>
