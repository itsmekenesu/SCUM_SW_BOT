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

# Copy all application code.
COPY . .

# Expose the port (make sure it matches the PORT environment variable, e.g., 8079).
EXPOSE 8079

# Startup command.
CMD ["python", "main.py"]
