# Newer Debian base (no 404 issues)
FROM python:3.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    ffmpeg \
    mediainfo \
    aria2 \
  && rm -rf /var/lib/apt/lists/*

# Python deps (upgrade pip first)
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Ensure any leftover .session files from repo are gone (safety)
RUN find /app -maxdepth 1 -type f -name "*.session*" -delete || true

CMD ["python", "main.py"]
