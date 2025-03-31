FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy dependency file and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port 8080 for health checks
EXPOSE 8080

# Run the application using main.py as the entry point
CMD ["python", "main.py"]
