FROM python:3.9.7-slim-buster

# Optionally keep Python output unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Proper working directory
WORKDIR /app

# System dependencies (Debian/Ubuntu style)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    ffmpeg \
    aria2 \
  && rm -rf /var/lib/apt/lists/*

# Better layer caching: install Python deps first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

CMD ["python", "main.py"]
