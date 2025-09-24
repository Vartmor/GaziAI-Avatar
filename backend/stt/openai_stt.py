import os
import shutil
import subprocess
from openai import OpenAI
import tempfile

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    print("❗ Uyarı: OPENAI_API_KEY ortam değişkeni yok. Lütfen setx/open .env ile ayarla.")
client = OpenAI(api_key=OPENAI_KEY)


def _has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def _convert_to_wav(input_path: str, out_wav: str) -> bool:
    if not _has_ffmpeg():
        print("FFmpeg bulunamadı. Lütfen sisteminize FFmpeg yükleyin.")
        return False

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le", out_wav
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("ffmpeg dönüştürme başarılı!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg hatası: {e.stderr}")
        return False
    except Exception as e:
        print(f"ffmpeg çalıştırma hatası: {e}")
        return False


def transcribe_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # Geçici dosya için güvenli bir yol oluştur
    temp_dir = tempfile.gettempdir()
    temp_wav = os.path.join(temp_dir, "temp_audio.wav")

    # Desteklenen formatlar
    supported_formats = ['.wav', '.mp3', '.m4a', '.webm', '.ogg', '.flac', '.mp4', '.mpeg', '.mpga', '.oga']

    # Dosya uzantısını kontrol et
    file_ext = os.path.splitext(path)[1].lower()
    # Uzantı kontrolünü yumuşat: bilinmeyen uzantılarda bile işleme devam et
    supported_formats = list(set(supported_formats + [file_ext]))

    if file_ext not in supported_formats:
        print(f"Desteklenmeyen dosya formatı: {file_ext}")
        return "[Desteklenmeyen dosya formatı]"

    # Eğer dosya zaten WAV değilse dönüştür
    if True:
        if not _convert_to_wav(path, temp_wav):
            print("Dosya dönüştürme başarısız, orijinal dosyayı kullanmaya çalışıyor...")
            temp_wav = path
    else:
        temp_wav = path

    try:
        with open(temp_wav, "rb") as f:
            res = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="tr"  # Türkçe için dil belirt
            )

        text = res.text if hasattr(res, "text") else ""
        print(f"STT Başarılı: '{text}'")

        # Geçici dosyayı temizle
        if temp_wav != path and os.path.exists(temp_wav):
            os.remove(temp_wav)

        return text.strip()
    except Exception as e:
        print(f"STT Hatası: {e}")
        # Geçici dosyayı temizle
        if temp_wav != path and os.path.exists(temp_wav):
            os.remove(temp_wav)
        return "[Anlaşılamadı]"
