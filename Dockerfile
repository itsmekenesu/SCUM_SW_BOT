FROM python:3.11-slim

WORKDIR /app

# Install process manager
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Configure supervisor
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Use DigitalOcean's persistent storage path
RUN mkdir -p /workspace/.data

CMD ["/usr/bin/supervisord"]
