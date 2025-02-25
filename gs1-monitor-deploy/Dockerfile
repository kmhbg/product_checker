FROM python:3.9-slim

# Installera systempaket inklusive ImageMagick
RUN apt-get update && apt-get install -y \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Sätt arbetskatalogen
WORKDIR /app

# Kopiera requirements.txt först för att utnyttja Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera resten av applikationen
COPY . .

# Create volume mount point
VOLUME ["/data"]

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "web_status.py"]