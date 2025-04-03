FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp && chmod 777 /tmp

CMD ["gunicorn", "--bind", "0.0.0.0:8079", "--workers", "1", "--timeout", "120", "--preload", "vps_server:app"]
