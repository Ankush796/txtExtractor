# Newer Debian base (no 404 issues)
FROM python:3.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# System deps (ffmpeg + mediainfo yahin se aayenge)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    ffmpeg \
    mediainfo \
    aria2 \
  && rm -rf /var/lib/apt/lists/*

# Faster, deterministic pip
RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Telegram bot = background worker (no HTTP port needed)
CMD ["python", "main.py"]
