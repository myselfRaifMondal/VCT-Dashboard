#!/bin/bash

echo "🎯 VCT Dashboard Startup"
echo "======================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run from the project directory."
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python not found. Please install Python 3.8+."
    exit 1
fi

# Check if required files exist
if [ ! -f "vct.db" ]; then
    echo "⚠️  Warning: vct.db not found. You may need to import data first."
    echo "   Run: python scripts/import_large_files.py"
fi

echo "🚀 Starting VCT Dashboard with External Access..."
echo ""

# Start the reliable tunnel
python reliable_tunnel.py
