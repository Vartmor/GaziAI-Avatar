# backend/main.py
import os
import sys
import base64

import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Ensure project root is on sys.path so backend.* imports resolve during Docker builds
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.stt.openai_stt import transcribe_file
from backend.llm.openai_llm_api import ask_openai
from backend.tts.tts_api import tts_to_file

# Optional subsystems: keep flags so we can degrade gracefully if modules fail later
try:
    stt_available = True
except ImportError:
    print("Warning: STT modules failed to load")
    stt_available = False

try:
    llm_available = True
except ImportError:
    print("Warning: LLM modules failed to load")
    llm_available = False

ENABLE_CV = os.getenv("ENABLE_COMPUTER_VISION", "true").lower() == "true"
CV_MODE = os.getenv("CV_MODE", "full").lower()
if CV_MODE not in {"full", "lite"}:
    CV_MODE = "full"

CV_PLACEHOLDER = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='360'>"
    "<rect width='100%' height='100%' fill='#4a5568'/>"
    "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='white' font-size='24'>"
    "Computer vision disabled</text></svg>"
)

UnifiedDetectionSystem = None
cv_available = False
if ENABLE_CV:
    if CV_MODE == "lite":
        cv_available = True
        print("Computer Vision lite mode active: streaming raw camera frames")
    else:
        try:
            from computer_vision.unified_detection import UnifiedDetectionSystem  # type: ignore

            cv_available = True
            print("Computer Vision modules loaded successfully")
        except ImportError as exc:
            print(f"Warning: Computer Vision modules failed to load: {exc}")
else:
    print("Computer Vision disabled via configuration")

app = Flask(__name__)
app.secret_key = "gazi-ai-secret-key"

cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
if cors_origins_raw and cors_origins_raw != "*":
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
    if not cors_origins:
        cors_origins = "*"
else:
    cors_origins = "*"

CORS(app, resources={r"/api/*": {"origins": cors_origins}, r"/audio/*": {"origins": cors_origins}})

RESULT_DIR = os.environ.get("RESULT_DIR", os.path.join(root_dir, "result"))
os.makedirs(RESULT_DIR, exist_ok=True)
app.config["UPLOAD_FOLDER"] = RESULT_DIR
app.config["RESULT_DIR"] = RESULT_DIR
max_size_mb = os.getenv("MAX_AUDIO_SIZE_MB", "10")
try:
    app.config["MAX_CONTENT_LENGTH"] = int(max_size_mb) * 1024 * 1024
except ValueError:
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

detection_system = None
if cv_available and CV_MODE == "full" and UnifiedDetectionSystem is not None:
    try:
        detection_system = UnifiedDetectionSystem()
        print("Computer Vision runtime started")
    except Exception as exc:
        print(f"Error starting Computer Vision runtime: {exc}")
        cv_available = False
elif cv_available and CV_MODE == "lite":
    print("Computer Vision lite mode: skipping heavy detection pipeline")


def initialize_camera():
    try:
        if cv_available and detection_system:
            if detection_system.start_camera():
                print("Camera started successfully")
                return True
            print("Camera could not be started")
            return False
        return False
    except Exception as exc:
        print(f"Camera start error: {exc}")
        return False


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/")
def index():
    return render_template("index.html", cv_available=cv_available)


@app.route("/api/upload_audio", methods=["POST"])
def upload_audio():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file"}), 400

        audio_file = request.files["audio"]
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], f"temp_{filename}")
        audio_file.save(temp_path)

        try:
            transcript = transcribe_file(temp_path) if stt_available else "[STT disabled]"
            print(f"Transcript: {transcript}")
        except Exception as exc:
            print(f"STT error: {exc}")
            transcript = "[STT error]"

        try:
            response_text = ask_openai(transcript) if llm_available else "Hello, how can I help?"
            print(f"LLM response: {response_text}")
        except Exception as exc:
            print(f"LLM error: {exc}")
            response_text = "There was an error, please try again."

        try:
            wav_path = tts_to_file(response_text)
            if not wav_path or not os.path.exists(wav_path):
                raise RuntimeError("TTS output missing")

            audio_filename = os.path.basename(wav_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            return jsonify({"audio_url": "/audio/" + audio_filename, "cues_json": None})
        except Exception as exc:
            print(f"TTS error: {exc}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        print(f"Upload error: {exc}")
        return jsonify({"error": "Server error"}), 500


@app.route("/audio/<path:filename>")
def get_audio(filename):
    safe_name = os.path.basename(filename)
    return send_from_directory(RESULT_DIR, safe_name, mimetype="audio/wav", as_attachment=False, conditional=True)


@app.route("/api/process_frame", methods=["POST"])
def process_frame():
    if not cv_available:
        return jsonify({
            "success": True,
            "objects": [],
            "hands": 0,
            "faces": 0,
            "pose_detected": False,
            "fingers": 0,
            "gesture": None,
            "fps": 0,
            "processed_frame": CV_PLACEHOLDER,
            "cv_mode": CV_MODE,
        })

    data = request.get_json(silent=True) or {}
    frame_data = data.get("frame", "")

    if CV_MODE == "lite" or not detection_system:
        if not frame_data:
            return jsonify({"success": False, "error": "Missing frame data", "cv_mode": CV_MODE}), 400
        processed_frame = frame_data if frame_data.startswith("data:image") else f"data:image/jpeg;base64,{frame_data}"
        return jsonify({
            "success": True,
            "objects": [],
            "hands": 0,
            "faces": 0,
            "pose_detected": False,
            "fingers": 0,
            "gesture": None,
            "fps": 0,
            "processed_frame": processed_frame,
            "cv_mode": CV_MODE,
        })

    try:
        if frame_data.startswith("data:image/jpeg;base64,"):
            frame_data = frame_data.split(",", 1)[1]

        frame_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        processed_frame, results = detection_system.object_detector.detect_objects(frame)

        _, buffer = cv2.imencode(".jpg", processed_frame)
        processed_frame_base64 = base64.b64encode(buffer).decode("utf-8")

        return jsonify({
            "success": True,
            "objects": results.get("objects", []),
            "hands": results.get("hands", 0),
            "faces": results.get("faces", 0),
            "pose_detected": results.get("pose_detected", False),
            "fingers": results.get("fingers", 0),
            "gesture": results.get("gesture", None),
            "fps": results.get("fps", 0),
            "processed_frame": f"data:image/jpeg;base64,{processed_frame_base64}",
            "cv_mode": CV_MODE,
        })

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "cv_mode": CV_MODE})


@app.route("/api/get_detection_results")
def get_detection_results():
    if not cv_available:
        return jsonify({
            "success": True,
            "objects": [],
            "hands": 0,
            "faces": 0,
            "pose_detected": False,
            "fps": 0,
            "cv_mode": CV_MODE,
        })

    if CV_MODE == "lite" or not detection_system:
        return jsonify({
            "success": True,
            "objects": [],
            "hands": 0,
            "faces": 0,
            "pose_detected": False,
            "fps": 0,
            "cv_mode": CV_MODE,
        })

    try:
        results = detection_system.get_detection_results()
        return jsonify({
            "success": True,
            "objects": results.get("objects", []),
            "hands": results.get("hands", 0),
            "faces": results.get("faces", 0),
            "pose_detected": results.get("pose_detected", False),
            "fps": results.get("fps", 0),
            "cv_mode": CV_MODE,
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "cv_mode": CV_MODE})


def shutdown_detection_system(exception=None):
    pass


print("Application starting...")
if __name__ == "__main__":
    if False and initialize_camera():
        print("Camera started")
    else:
        print("Camera could not be started")

    app.run(debug=True, host="0.0.0.0", port=5000)
