FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Proper command to run both services
CMD bash -c \
    "gunicorn --bind 0.0.0.0:8079 app.vps_server:app & \
    python -u app/discord_bot.py & \
    wait"
