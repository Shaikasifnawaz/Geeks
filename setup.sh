#!/bin/bash
# Linux/Mac Setup Script for NCAAFB Backend Pipeline

echo "========================================"
echo "NCAAFB Backend Pipeline - Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/3] Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "[2/3] Setting up environment configuration..."
python3 backend/scripts/create_env.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create .env file"
    exit 1
fi

echo ""
echo "[3/3] Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure PostgreSQL is running"
echo "2. Run: python3 backend/main.py"
echo ""

