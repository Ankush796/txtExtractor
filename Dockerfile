# Newer Debian base (no 404 issues)
FROM python:3.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# System deps (ffmpeg + mediainfo yahin se aayenge; pip se nahi)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    ffmpeg \
    mediainfo \
    aria2 \
  && rm -rf /var/lib/apt/lists/*

# (Optional) Update pip to latest for better resolver
RUN python -m pip install --upgrade pip

# Install Python deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . .

# IMPORTANT: ensure old sessions aren't baked into image
# If you keep file-based sessions, add a .dockerignore entry:
# *.session
# *.session-journal

CMD ["python", "main.py"]
