# tts/tts_api.py (Temizlenmiş, duplike sil)
import os
import re
import time
import unicodedata
from openai import OpenAI

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULT_DIR = os.environ.get("RESULT_DIR", os.path.join(ROOT_DIR, "result"))
os.makedirs(RESULT_DIR, exist_ok=True)


def _slugify(text: str) -> str:
    try:
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        pass
    text = re.sub(r'[^A-Za-z0-9]+', '_', text).strip('_')
    return text or 'response'

def tts_to_file(text: str) -> str:
    base = _slugify(text[:32])
    filename = os.path.join(RESULT_DIR, f"{base}_{int(time.time())}.wav")
    try:
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="ash",
            input=text,
            instructions="Speak like a cheerful, warm-hearted uncle who is full of life. Always sound friendly, approachable, and kind. Use a light,smiling tone, and occasionally add a gentle chuckle. Speak clearly, softening and rounding your words. Make the listener feel comfortable, safe, and happy. Maintain a positive, uplifting energy throughout the conversation."
        )
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename
    except Exception as e:
        print("❌ TTS hatası:", e)
        return ""
