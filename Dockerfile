FROM python:3.10-slim

# Installera systempaket inklusive ImageMagick
RUN apt-get update && apt-get install -y \
    imagemagick \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Konfigurera ImageMagick för att tillåta PDF-konvertering
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

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

# Sätt miljövariabler
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web_status.py

# Command to run the application
CMD ["python", "web_status.py"]