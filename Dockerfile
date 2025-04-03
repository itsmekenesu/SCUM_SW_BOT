FROM python:3.11-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory and set permissions
RUN mkdir -p /tmp/data && chmod 777 /tmp/data

# Single process entrypoint
CMD ["gunicorn", "--bind", "0.0.0.0:8079", "--workers", "1", "--timeout", "120", "--preload", "vps_server:app"]
