#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🔹 Updating apt repositories..."
sudo apt-get update -y

echo "🔹 Installing Tesseract and Poppler..."
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin poppler-utils

echo "🔹 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completed successfully!"
