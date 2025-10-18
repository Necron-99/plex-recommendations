#!/bin/bash

# Setup script for Plex Data Exporter
# Creates a virtual environment and installs dependencies

echo "🐍 Setting up Python virtual environment for Plex Data Exporter..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install python3 and python3-venv:"
    echo "   sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Check if python3-venv is available
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ python3-venv is not installed. Please install it:"
    echo "   sudo apt install python3-venv"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv plex-venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source plex-venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "🚀 To use the Plex Data Exporter:"
echo "   1. Activate the virtual environment:"
echo "      source plex-venv/bin/activate"
echo ""
echo "   2. Run the exporter:"
echo "      python plex-data-exporter.py"
echo ""
echo "   3. Deactivate when done:"
echo "      deactivate"
echo ""
echo "💡 Tip: You can also run the exporter directly:"
echo "      ./plex-venv/bin/python plex-data-exporter.py"
