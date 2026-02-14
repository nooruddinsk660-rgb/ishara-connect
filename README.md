
# Ishara Connect - AI Sign Language Interpreter 🖐️🤖

**Ishara Connect** is an advanced, real-time sign language interpretation system powered by AI and Computer Vision. It translates hand gestures into spoken language (Bengali, Hindi, English) to bridge the communication gap for the deaf and mute community.


## 🌟 Key Features

*   **Real-Time Gesture Recognition**: Uses MediaPipe and a custom Random Forest model to detect 30+ gestures instantly.
*   **Multi-Language Support**: Translates gestures into **Bengali**, **Hindi**, and **English**.
*   **Polite Mode**: Toggle between casual and formal/polite speech output (e.g., "Water" vs. "Could I please have some water?").
*   **Cyberpunk Glassmorphism UI**: A stunning, modern interface with neon accents, animated gradients, and glassmorphism cards.
*   **Robotic Hand Visualization**: Features a high-tech, glowing robotic hand tracking effect in the video feed.
*   **Voice & Camera Controls**: Integrated toggle buttons to mute audio or turn off the camera feed.
*   **Theme System**: Switch between a dark "Cyberpunk" theme and a clean "Light" mode.

## 🛠️ Tech Stack

*   **Frontend**: HTML5, CSS3 (Glassmorphism, Animations), JavaScript (Fetch API)
*   **Backend**: Python (Flask)
*   **AI/ML**: OpenCV, MediaPipe, Scikit-Learn (Random Forest), NumPy, Pandas
*   **Audio**: gTTS (Google Text-to-Speech) / Pre-generated MP3s

## 📂 Project Structure

```
ishara-connect/
├── app.py                  # Main Flask application & Inference logic
├── data_collector.py       # Script to collect training data via webcam
├── train_model.py          # Script to train the Random Forest model
├── utils.py                # Helper functions (feature extraction)
├── generate_premium_audio.py # Script to generate TTS audio files
├── model.p                 # Trained AI Model (Pickle file)
├── data.csv                # Collected dataset (Features & Labels)
├── static/
│   ├── css/                # Stylesheets (style.css)
│   ├── audio/              # Generated audio files (organized by language)
│   └── images/             # Static assets
└── templates/
    ├── index.html          # Main dashboard
    └── components/         # HTML components (header, camera, gestures, scripts)
```

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   Webcam

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/ishara-connect.git
    cd ishara-connect
    ```

2.  **Install Dependencies**:
    ```bash
    pip install flask opencv-python mediapipe scikit-learn pandas numpy gtts
    ```

### Usage

1.  **Run the Application**:
    ```bash
    python app.py
    ```

2.  **Open in Browser**:
    Navigate to `http://127.0.0.1:5000`

3.  **Interact**:
    *   Show gestures to the camera.
    *   Click the **Language Icon** to change languages.
    *   Click the **Polite Toggle** for formal speech.
    *   Use the **Camera/Sound** buttons to control the feed/audio.

## 🧠 Training Your Own Gestures

1.  **Configure Classes**:
    Open `data_collector.py` and modify `TARGET_CLASSES` to include the gestures you want to record.
    ```python
    TARGET_CLASSES = ["MyNewGesture"]
    ```

2.  **Collect Data**:
    Run the collector and follow the on-screen prompts.
    ```bash
    python data_collector.py
    ```

3.  **Train Model**:
    Run the training script to update `model.p`.
    ```bash
    python train_model.py
    ```

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License.
