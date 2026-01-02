#!/bin/bash
# Start Risk Runners development server

echo "🚀 Starting Risk Runners development server..."

# Update cache-busting parameters for JavaScript files
echo "🔄 Updating cache-busting parameters..."
if command -v python3 &> /dev/null; then
    python3 update-cache-busting.py
elif command -v python &> /dev/null; then
    python update-cache-busting.py
else
    echo "⚠️  Python not found - skipping cache-busting update"
fi

echo ""

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