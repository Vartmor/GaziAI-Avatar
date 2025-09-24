FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY backend ./backend
COPY computer_vision ./computer_vision
COPY docs ./docs

ENV RESULT_DIR=/app/result
RUN mkdir -p "$RESULT_DIR"

EXPOSE 5000

CMD ["gunicorn", "backend.main:app", "--bind", "0.0.0.0:5000", "--workers", "1"]
