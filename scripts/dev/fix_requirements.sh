#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

cd backend

# Aktivácia venv
source venv/bin/activate

# Oprava requirements - zmena python-email-validator na email-validator
sed -i 's/python-email-validator==2.0.0/email-validator==2.0.0/g' requirements.txt

# Inštalácia závislostí
pip install --upgrade pip
pip install -r requirements.txt

# Inštalácia chýbajúcich modulov
pip install prometheus-client python-json-logger

cd ..
echo "Závislosti úspešne nainštalované"
