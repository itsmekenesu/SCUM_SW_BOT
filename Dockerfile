FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libnacl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data && chmod 777 /data

CMD ["gunicorn", "--bind", "0.0.0.0:8079", "--workers", "1", "--timeout", "120", "--preload", "scum_bot:app"]
