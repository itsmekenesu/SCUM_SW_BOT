FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start both services in parallel
CMD gunicorn --bind 0.0.0.0:8079 app.vps_server:app & \
    python -u app/discord_bot.py
