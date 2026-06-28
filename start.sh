#!/bin/bash

# Video Summarizer - Quick Start Script

echo "🎬 Video Summarizer - Starting Application"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the video_summarizer directory"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import cv2, whisper, flask" 2>/dev/null; then
    echo "⚠️  Dependencies not found. Installing..."
    pip3 install -r requirements.txt
fi

echo "✅ Dependencies ready"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads output temp

echo "✅ Setup complete"
echo ""

# Display instructions
echo "🚀 Starting Flask web application..."
echo ""
echo "📝 Instructions:"
echo "   1. Open your browser to: http://localhost:5001"
echo "   2. Drag and drop a video file or click to upload"
echo "   3. Wait for processing to complete"
echo "   4. Download your generated PowerPoint!"
echo ""
echo "💡 Tips:"
echo "   - Supported formats: MP4, AVI, MOV, MKV"
echo "   - Maximum file size: 500MB"
echo "   - First run may take longer (Whisper model download)"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""
echo "=========================================="
echo ""

# Start the application
python3 app.py
