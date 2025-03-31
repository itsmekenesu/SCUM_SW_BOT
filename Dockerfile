FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the dependency file and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Run the bot using the entry point
CMD ["python", "main.py"]
