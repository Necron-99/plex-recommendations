#!/bin/bash

# Quick run script for Plex Data Exporter
# Automatically activates virtual environment and runs the exporter

echo "🎬 Plex Data Exporter - Quick Run"
echo "================================="

# Check if virtual environment exists
if [ ! -d "plex-venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   ./setup-venv.sh"
    exit 1
fi

# Activate virtual environment and run exporter
echo "🔧 Activating virtual environment..."
source plex-venv/bin/activate

echo "🚀 Running Plex Data Exporter..."
echo ""

# Run the exporter with any passed arguments
python plex-data-exporter.py "$@"

echo ""
echo "✅ Exporter completed!"
echo "💡 Virtual environment is still active. Run 'deactivate' to exit."
