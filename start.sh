#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "====================================="
echo "  Welcome to OpenTax! Launching...   "
echo "====================================="

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install Node.js."
    exit 1
fi

# Check if python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Error: python3 is not installed. Please install Python."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 1. Setup Backend
echo "--> Checking Backend Dependencies..."
cd backend

if [ ! -d "venv" ]; then
    echo "    Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements quietly
pip install -r requirements.txt > /dev/null 2>&1

cd ..

# 2. Setup Frontend
echo "--> Checking Frontend Dependencies..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "    Installing Node modules (this might take a minute)..."
    npm install > /dev/null 2>&1
fi

echo "    Building Frontend application..."
npm run build > /dev/null 2>&1

cd ..

# 3. Launch App
echo "--> Starting Server..."
echo ""
echo "    App is starting! It will open in your browser automatically."
echo "    (Keep this window open while using OpenTax. Press Ctrl+C to quit)"
echo "====================================="

cd backend

# Function to open browser after server starts
open_browser() {
    sleep 2
    if command -v open &> /dev/null; then
        open http://localhost:8000
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000
    elif command -v start &> /dev/null; then
        start http://localhost:8000
    fi
}

open_browser &

# Start the FastAPI server
$PYTHON_CMD main.py
