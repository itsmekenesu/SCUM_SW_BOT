FROM python:3.10-slim

# Set the working directory.
WORKDIR /app

# Copy and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files.
COPY . .

# Expose port 8080 for the health check.
EXPOSE 8080

# Run the application.
CMD ["python", "main.py"]
