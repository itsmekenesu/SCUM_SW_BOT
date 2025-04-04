FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libnacl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory
RUN mkdir -p /data && chown -R 1000:1000 /data

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:8079/api/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8079", "--workers", "1", "--timeout", "120", "--preload", "scum_bot:app"]
