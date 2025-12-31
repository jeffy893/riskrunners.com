#!/bin/bash
# Start Risk Runners development server

echo "🚀 Starting Risk Runners development server..."

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    python3 serve.py
elif command -v python &> /dev/null; then
    python serve.py
else
    echo "❌ Python is not installed or not in PATH"
    echo "Please install Python 3 to run the development server"
    exit 1
fi