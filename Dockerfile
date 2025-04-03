FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create required directories with proper permissions
RUN mkdir -p \
    /var/log/supervisor \
    /workspace/.data \
    && chmod 755 /workspace/.data

# Verify SQLite database path
RUN echo "SQLite path: /workspace/.data/bots.db" && \
    touch /workspace/.data/bots.db && \
    chmod 644 /workspace/.data/bots.db

COPY supervisord.conf /etc/supervisor/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
