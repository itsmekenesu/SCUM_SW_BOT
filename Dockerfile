FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Python packages [[5]][[7]]
RUN apt-get update && apt-get install -y \
    build-essential \  # Required for compiling packages like pynacl [[5]]
    gcc \
    libffi-dev \
    libnacl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create data directory for SQLite [[6]]
RUN mkdir -p /data && chown -R 1000:1000 /data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Healthcheck for container monitoring [[1]][[4]]
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:8079/api/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8079", "--workers", "1", "--timeout", "120", "--preload", "scum_bot:app"]
