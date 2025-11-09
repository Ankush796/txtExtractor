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

# Faster, reliable pip
RUN python -m pip install --upgrade pip

# Install Python deps first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Default command
CMD ["python", "main.py"]
