# backend/main.py
import sys
import os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Root (Avatar Project/)
sys.path.append(root_dir)  # Root ekle, computer_vision için

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
from werkzeug.utils import secure_filename
import base64
import cv2
import numpy as np
import time
from backend.stt.openai_stt import transcribe_file  # Backend/ altından
from backend.llm.openai_llm_api import ask_openai
from backend.tts.tts_api import tts_to_file

# Gerekli modülleri import etmeyi dene
try:
    stt_available = True
except ImportError:
    print("⚠️ STT modülleri yüklenemedi")
    stt_available = False

try:
    llm_available = True
except ImportError:
    print("⚠️ LLM modülleri yüklenemedi")
    llm_available = False


ENABLE_CV = os.getenv('ENABLE_COMPUTER_VISION', 'true').lower() == 'true'
CV_MODE = os.getenv('CV_MODE', 'full').lower()
if CV_MODE not in {'full', 'lite'}:
    CV_MODE = 'full'
CV_PLACEHOLDER = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='360'><rect width='100%' height='100%' fill='#4a5568'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='white' font-size='24'>Computer vision disabled</text></svg>"

# Computer Vision modulleri
cv_available = False
if ENABLE_CV:
    if CV_MODE == 'lite':
        cv_available = True
        print("Computer Vision lite mode active: streaming raw camera frames")
    else:
        try:
            from computer_vision.unified_detection import UnifiedDetectionSystem  # Root'tan
            cv_available = True
            print("Computer Vision modulleri basariyla yuklendi!")
        except ImportError as e:
            print(f"Uyari: Computer Vision modulleri yuklenemedi: {e}")
            cv_available = False
else:
    print("Computer Vision modulleri konfigurasyon ile devre disi")

app = Flask(__name__)
app.secret_key = 'gazi-ai-secret-key'

cors_origins_raw = os.getenv('CORS_ORIGINS', '*')
if cors_origins_raw and cors_origins_raw != '*':
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(',') if origin.strip()]
    if not cors_origins:
        cors_origins = '*'
else:
    cors_origins = '*'

CORS(app, resources={r"/api/*": {"origins": cors_origins}, r"/audio/*": {"origins": cors_origins}})

RESULT_DIR = os.environ.get('RESULT_DIR', os.path.join(root_dir, 'result'))
os.makedirs(RESULT_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = RESULT_DIR
app.config['RESULT_DIR'] = RESULT_DIR
max_size_mb = os.getenv('MAX_AUDIO_SIZE_MB', '10')
try:
    app.config['MAX_CONTENT_LENGTH'] = int(max_size_mb) * 1024 * 1024
except ValueError:
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024


# Global detection system - sadece bir kez initialize et
detection_system = None
if cv_available and CV_MODE == 'full':
    try:
        detection_system = UnifiedDetectionSystem()
        print("Computer Vision modulleri basariyla baslatildi!")
    except Exception as e:
        print(f"Hata: Computer Vision baslatma hatasi: {e}")
        cv_available = False
elif cv_available and CV_MODE == 'lite':
    print("Computer Vision lite mode: skipping heavy detection pipeline")

@app.route("/audio/<path:filename>")
def get_audio(filename):
    safe_name = os.path.basename(filename)
    return send_from_directory(RESULT_DIR, safe_name, mimetype='audio/wav', as_attachment=False, conditional=True)



# CV route'lar aynı kalsın...


@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    if not cv_available:
        return jsonify({
            'success': True,
            'objects': [],
            'hands': 0,
            'faces': 0,
            'pose_detected': False,
            'fingers': 0,
            'gesture': None,
            'fps': 0,
            'cv_mode': CV_MODE,
            'processed_frame': CV_PLACEHOLDER
        })

    try:
        data = request.get_json()
        frame_data = data.get('frame', '')

        if CV_MODE == 'lite' or not detection_system:
            if not frame_data.startswith('data:image'):
                processed_frame = f"data:image/jpeg;base64,{frame_data}"
            else:
                processed_frame = frame_data
            return jsonify({
                'success': True,
                'objects': [],
                'hands': 0,
                'faces': 0,
                'pose_detected': False,
                'fingers': 0,
                'gesture': None,
                'fps': 0,
                'cv_mode': CV_MODE,
                'processed_frame': processed_frame
            })

        if frame_data.startswith('data:image/jpeg;base64,'):
            frame_data = frame_data.split(',')[1]

        frame_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        processed_frame, results = detection_system.object_detector.detect_objects(frame)

        _, buffer = cv2.imencode('.jpg', processed_frame)
        processed_frame_base64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'success': True,
            'objects': results.get('objects', []),
            'hands': results.get('hands', 0),
            'faces': results.get('faces', 0),
            'pose_detected': results.get('pose_detected', False),
            'fingers': results.get('fingers', 0),
            'gesture': results.get('gesture', None),
            'fps': results.get('fps', 0),
            'cv_mode': CV_MODE,
            'processed_frame': f"data:image/jpeg;base64,{processed_frame_base64}"
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'cv_mode': CV_MODE})

@app.route('/api/get_detection_results')
def get_detection_results():
    if not cv_available:
        return jsonify({
            'success': True,
            'objects': [],
            'hands': 0,
            'faces': 0,
            'pose_detected': False,
            'fps': 0,
            'cv_mode': CV_MODE
        })

    if CV_MODE == 'lite' or not detection_system:
        return jsonify({
            'success': True,
            'objects': [],
            'hands': 0,
            'faces': 0,
            'pose_detected': False,
            'fps': 0,
            'cv_mode': CV_MODE
        })

    try:
        results = detection_system.get_detection_results()
        return jsonify({
            'success': True,
            'objects': results.get('objects', []),
            'hands': results.get('hands', 0),
            'faces': results.get('faces', 0),
            'pose_detected': results.get('pose_detected', False),
            'fps': results.get('fps', 0),
            'cv_mode': CV_MODE
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'cv_mode': CV_MODE})

def shutdown_detection_system(exception=None):
    pass

print("Uygulama başlıyor...")
# initialize_camera()
if __name__ == "__main__":
    # Uygulama başlarken kamerayı başlat
    if False and initialize_camera():
        print("Kamera başlatıldı")
    else:
        print("Kamera başlatılamadı")

    app.run(debug=True, host="0.0.0.0", port=5000)

