FROM python:3.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg espeak-ng tesseract-ocr ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.lock requirements-voice.lock /app/
RUN pip install --no-cache-dir -r requirements.lock -r requirements-voice.lock
COPY api /app/api
ENV PYTHONPATH=/app/api
RUN useradd --uid 10001 --create-home studio
USER studio
CMD ["python", "-m", "uvicorn", "flamingo_next_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
