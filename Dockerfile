FROM python:3.10-slim

# Set the working directory.
WORKDIR /app

# Copy and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files.
COPY . .

# Expose port 8079 for the health check.
EXPOSE 8079

# Run the application.
CMD ["python", "main.py"]
