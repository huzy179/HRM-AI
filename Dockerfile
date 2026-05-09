FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ANONYMIZED_TELEMETRY=False \
    POSTHOG_DISABLED=1

WORKDIR /app

# System deps:
# - tesseract-ocr: OCR for scanned PDFs
# - libtesseract-dev: runtime libs
# - gcc/g++: some pip wheels may need compilation (keep minimal for now)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-vie \
        libtesseract-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY . /app

EXPOSE 8000 8501

# Commands are set per-service in docker-compose.yml
