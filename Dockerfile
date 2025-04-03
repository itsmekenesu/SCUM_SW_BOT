FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (no build tools needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use a proper process manager for multiple services
CMD bash -c \
    "gunicorn --bind 0.0.0.0:8079 --access-logfile - app.vps_server:app & \
    python -u app/discord_bot.py & \
    wait"
