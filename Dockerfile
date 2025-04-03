# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Single process model
CMD ["gunicorn", "--bind", "0.0.0.0:8079", "--workers", "1", "--timeout", "120", "app.vps_server:app"]
