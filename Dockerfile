FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory in container's ephemeral storage
RUN mkdir -p /data && \
    chmod 755 /data

CMD ["gunicorn", "--bind", "0.0.0.0:8079", "app.vps_server:app"]
