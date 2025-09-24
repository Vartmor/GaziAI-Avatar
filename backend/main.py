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

# Computer Vision modulleri
cv_available = False
if ENABLE_CV:
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
if cv_available:
    try:
        detection_system = UnifiedDetectionSystem()
        print("Computer Vision modulleri basariyla baslatildi!")
    except Exception as e:
        print(f"Hata: Computer Vision baslatma hatasi: {e}")
        cv_available = False

# Ses dosyaları buraya kaydedilecek
# Kamera başlatma fonksiyonu
def initialize_camera():
    try:
        if cv_available and detection_system:
            if detection_system.start_camera():
                print("Kamera başarıyla başlatıldı")
                return True
            else:
                print("Kamera başlatılamadı")
                return False
        return False
    except Exception as e:
        print(f"Kamera başlatma hatası: {e}")
        return False



@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route("/")
def index():
    return render_template("index.html", cv_available=cv_available)


@app.route('/api/upload_audio', methods=['POST'])
def upload_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400

        audio_file = request.files['audio']

        # Güvenli dosya adı ve geçici kaydetme
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        audio_file.save(temp_path)

        # STT
        try:
            transcript = transcribe_file(temp_path) if stt_available else "[STT Modülü Yok]"
            print(f"Transkript: {transcript}")
        except Exception as e:
            print(f"STT hatası: {e}")
            transcript = "[STT Hatası]"

        # LLM
        try:
            response_text = ask_openai(transcript) if llm_available else "Merhaba, nasılsın?"
            print(f"LLM Yanıtı: {response_text}")
        except Exception as e:
            print(f"LLM hatası: {e}")
            response_text = "Bir hata oluştu, tekrar deneyin."

        # TTS (Rhubarb'sız, dosyaya yazan API)
        try:
            wav_path = tts_to_file(response_text)
            if not wav_path or not os.path.exists(wav_path):
                raise RuntimeError('TTS output missing')

            audio_filename = os.path.basename(wav_path)

            # Geçici dosyayı sil
            if os.path.exists(temp_path):
                os.remove(temp_path)

            # cues_json artık opsiyonel (random lipsync kullanıyoruz)
            return jsonify({'audio_url': '/audio/' + audio_filename, 'cues_json': None})
        except Exception as e:
            print(f'TTS hatas�: {e}')
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Genel upload hatası: {e}")
        return jsonify({'error': 'Sunucu hatası'}), 500

@app.route("/audio/<path:filename>")
def get_audio(filename):
    # Güvenlik ve uyumluluk: sadece dosya adını kullan
    safe_name = os.path.basename(filename)
    # Doğru içerik türü ve range desteği
    return send_from_directory(RESULT_DIR, safe_name, mimetype='audio/wav', as_attachment=False, conditional=True)

# CV route'lar aynı kalsın...
@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    if not cv_available or not detection_system:
        return jsonify({'success': False, 'error': 'CV modülü yüklenemedi'})

    try:
        data = request.get_json()
        frame_data = data.get('frame', '')

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
            'processed_frame': f"data:image/jpeg;base64,{processed_frame_base64}"
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_detection_results')
def get_detection_results():
    if not cv_available or not detection_system:
        return jsonify({'success': False, 'error': 'CV modülü yüklenemedi'})

    try:
        results = detection_system.get_detection_results()
        return jsonify({
            'success': True,
            'objects': results.get('objects', []),
            'hands': results.get('hands', 0),
            'faces': results.get('faces', 0),
            'pose_detected': results.get('pose_detected', False),
            'fps': results.get('fps', 0)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Not: Her istek sonunda kamerayı durdurmak performansı bozar. Kapatmayı uygulama
# kapanışında yönetmek daha doğru. Bu yüzden teardown hook devre dışı.
# import atexit; atexit.register(lambda: detection_system and detection_system.stop_camera())
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

