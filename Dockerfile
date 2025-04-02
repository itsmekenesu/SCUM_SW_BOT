FROM python:3.10-slim

# Install system dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . .

# Expose the port that the SCUM BOT’s Flask server uses.
EXPOSE 8079

# Startup command.
CMD ["python", "main.py"]
