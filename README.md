# Avatar Project – 3D Konuşan Avatar (React + R3F + Flask)

Bu proje; mikrofonla konuştuğunuz metni OpenAI ile çözüp (STT), LLM ile yanıtlayıp (Chat), sesi üreterek (TTS) 3D avatarın dudak hareketleri eşliğinde oynatır. Ön yüzde React + Vite + react-three-fiber, arka planda Flask kullanır. Bilgisayar kameranızdan gelen görüntü de basit bir CV pipeline’ı ile işlenir.

Ön uç (port 5173) → proxy → Arka uç (Flask, port 5000)

---

## Özellikler

* 3D Avatar (React Three Fiber, drei, three)
* Ses Kaydı → STT (OpenAI Whisper)
* LLM Yanıtı (OpenAI Chat Completions)
* TTS Ses Üretimi (OpenAI gpt-4o-mini-tts)
* Rhubarb Lip Sync ile viseme verisi üretimi (backend)
* Webcam görüntüsünü işleme (OpenCV + MediaPipe)

---

## Hızlı Başlangıç

* Gerekenler: Python 3.10+, Node.js 18+, FFmpeg, OpenAI API anahtarı
* 2 terminal açın: biri backend (Flask), biri frontend (Vite)


OS’e göre FFmpeg kurulumu:

* Windows

  * FFmpeg: `choco install ffmpeg` veya [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

* macOS

  * FFmpeg: `brew install ffmpeg` (Homebrew)
  
* Linux (Debian/Ubuntu tabanlı)

  * FFmpeg: `sudo apt update && sudo apt install ffmpeg`


---

## Kurulum – Windows

1. Repo'yu klonla

* `git clone <repo-url>`
* `cd Avatar Project`

2. Python ortamı (kök dizinde)

* `python -m venv .venv`
* `.\.venv\Scripts\activate`
* `pip install --upgrade pip`
* `pip install -r requirements.txt`

3. Ortam değişkenleri (.env)

* Kök klasörde `.env` dosyası oluşturun (varsa düzenleyin):

  * `OPENAI_API_KEY=...`
  
* İsteğe bağlı: PowerShell oturumunda geçici set → `$env:OPENAI_API_KEY="..."`

4. Backend’i başlatın

* `cd backend`
* `python main.py`
* Sunucu: `http://127.0.0.1:5000`

5. Frontend’i başlatın (yeni başka bir terminal)

* `cd frontend`
* `npm install`
* `npm run dev`
* Tarayıcı: `http://localhost:5173` (Vite, `/api` ve `/audio` isteklerini 5000’e proxy’ler)

---

## Kurulum – macOS

1. Depo

* `git clone <repo-url>`
* `cd Avatar Project`

2. Python ortamı (kök dizinde)

* `python3 -m venv .venv`
* `source .venv/bin/activate`
* `python -m pip install --upgrade pip`
* `pip install -r requirements.txt`

3. Ortam değişkenleri (.env)

* Kök klasörde `.env` oluşturun:

  * `OPENAI_API_KEY=...`
  
* Geçici set: `export OPENAI_API_KEY=...`

4. Backend’i başlatın

* `cd backend`
* `python main.py`
* Sunucu: `http://127.0.0.1:5000`

5. Frontend’i başlatın (yeni terminal)

* `cd frontend`
* `npm install`
* `npm run dev`
* Tarayıcı: `http://localhost:5173`

---

## Kurulum – Linux (Debian/Ubuntu tabanlı)

1. Depo

* `git clone <repo-url>`
* `cd Avatar Project`

2. Python ortamı (kök dizinde)

* `python3 -m venv .venv`
* `source .venv/bin/activate`
* `python -m pip install --upgrade pip`
* `pip install -r requirements.txt`

3. Ortam değişkenleri (.env)

* Kök klasörde `.env` oluşturun:

  * `OPENAI_API_KEY=...`
  
* Geçici set: `export OPENAI_API_KEY=...`

4. Backend’i başlatın

* `cd backend`
* `python main.py`
* Sunucu: `http://127.0.0.1:5000`

5. Frontend’i başlatın (yeni terminal)

* `cd frontend`
* `npm install`
* `npm run dev`
* Tarayıcı: `http://localhost:5173`

---

## Proje Yapısı (Özet)

* `backend/` – Flask API, STT/LLM/TTS, CV

  * `main.py` – Flask giriş noktası (port 5000)
  * `tts/tts_api.py` – gpt 4o mini tts 
  * `stt/openai_stt.py` – Whisper tabanlı STT (FFmpeg gerekir)
  * `llm/openai_llm_api.py` – Chat Completions
  * `computer_vision/` – OpenCV + MediaPipe iş hattı
* `frontend/` – React + Vite + R3F avatar

  * `npm run dev` – Vite (port 5173)
  * `vite.config.js` – `/api` & `/audio` proxy → `http://localhost:5000`
* `docs/` – referans ve notlar
* `requirements.txt` – Backend bağımlılıkları
* `.env` – API anahtarları ve yollar (commit etmeyin)

---

## Kullanım

* Frontend çalışırken tarayıcıda “Konuş” butonunu kullanın.
* Backend ses dosyasını alır → STT → LLM → TTS → sesi döndürür.
* Avatar idle iken arada Greeting (el sallama) yapar; konuşurken dudaklar hareket eder.

---

## Sorun Giderme

* Kamera/izin hatası

  * Tarayıcıdan kamera izni verin. Hâlâ olmuyorsa `frontend/src/components/CameraFeed/index.jsx`’te fallback görüntü devrededir.
* FFmpeg bulunamadı

  * FFmpeg’i sistem PATH’ine ekleyin (Windows: choco, macOS: brew, Linux: apt).
* Node/Vite uyumsuzluğu

  * Node 18+ kullanın. `npm install` sonrası `npm run dev`.
* Port çakışması

  * Backend: 5000, Frontend: 5173. Gerekirse `vite.config.js` veya `main.py` portlarını değiştirin.

---

## Yapi/Dagitim (opsiyonel)

* Frontend uretim derlemesi: `cd frontend && npm run build` (cikti `dist/`)
* Netlify icin: repoyu baglayip build ayarlarini base=`frontend`, command=`npm install && npm run build`, publish=`frontend/dist` olarak girin veya `netlify.toml` dosyasini kullanin.
* Netlify panelinde `VITE_API_BASE_URL` ortam degiskenini canli backend URL'i ile tanimlayin.
* Canli demo icin frontend `.env` dosyasinda `VITE_API_BASE_URL=https://backend-urz.example` seklinde bir URL tanimlayin.
* Backend icin gerekli ortam degiskenleri `backend/.env.example` dosyasinda listelidir (`OPENAI_API_KEY`, opsiyonel `CORS_ORIGINS`, `RESULT_DIR`).
* Docker ile calistirmak icin: `docker build -t avatar-backend .` ve `docker run -p 5000:5000 --env-file backend/.env avatar-backend`.
* Sunucunuzu gunicorn veya Render/Railway gibi bir PaaS uzerinde `gunicorn backend.main:app --bind 0.0.0.0:5000` komutu ile calistirin.
* FFmpeg eksikse, Dockerfile veya platform build scriptinde paket olarak ekleyin.


## Ortam Degiskenleri

| Bilesen | Degisken | Aciklama |
| --- | --- | --- |
| Backend | OPENAI_API_KEY | OpenAI servislerine erisim icin zorunlu |
| Backend | CORS_ORIGINS | Virgulle ayrilmis izinli origin listesi (`*` tum istemciler icin) |
| Backend | ENABLE_COMPUTER_VISION | `true` ise CV pipeline acik, `false` ile devre disi (daha az bellek) |
| Backend | RESULT_DIR | Uretilen ses dosyalarinin yazilacagi klasor (varsayilan `result/`) |
| Backend | MAX_AUDIO_SIZE_MB | Upload dosyalarinin maksimum boyutu (MB olarak, varsayilan 10) |
| Frontend | VITE_API_BASE_URL | Canli backend URL'si; bos birakilirsa tarayici ile ayni origin kullanilir |

---

## Güvenlik Notları

* `.env` dosyasını kesinlikle versiyon kontrolüne koymayın.
* API anahtarlarını yalnızca güvenli ortamlarda kullanın.

---

## Lisans

Bu repo eğitim ve demo amaçlıdır. Bağımlılıkların lisanslarına uyun.
