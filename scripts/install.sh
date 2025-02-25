#!/bin/bash

# Kontrollera om Docker är installerat
if ! command -v docker &> /dev/null; then
    echo "Docker är inte installerat. Installerar..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
fi

# Kontrollera om Docker Compose är installerat
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose är inte installerat. Installerar..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Skapa nödvändiga mappar
sudo mkdir -p /opt/gs1-monitor
sudo mkdir -p /opt/gs1-monitor/product_images
sudo mkdir -p /opt/gs1-monitor/logs
sudo mkdir -p /opt/gs1-monitor/backups

# Kopiera filer
sudo cp -r * /opt/gs1-monitor/

# Skapa .env fil om den inte finns
if [ ! -f /opt/gs1-monitor/.env ]; then
    sudo cp /opt/gs1-monitor/config/.env.example /opt/gs1-monitor/.env
    echo "Skapa .env fil från exempel..."
fi

# Sätt rättigheter
sudo chown -R 1000:1000 /opt/gs1-monitor

echo "Installation klar! Konfigurera .env filen och starta med:"
echo "cd /opt/gs1-monitor && docker-compose -f docker-compose.prod.yml up -d" 