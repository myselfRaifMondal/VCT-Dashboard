#!/bin/bash

echo "🚀 VCT Dashboard - External Access Setup"
echo "========================================"

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

echo "📍 Local Network IP: $LOCAL_IP"
echo ""

# Start Streamlit in the background
echo "🎯 Starting Streamlit app..."
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 &
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 3

# Check if Streamlit is running
if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ Streamlit is running successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Local:        http://localhost:8501"
    echo "   Network:      http://$LOCAL_IP:8501"
    echo ""
else
    echo "❌ Failed to start Streamlit"
    exit 1
fi

# Try different tunnel services
echo "🌍 Setting up external tunnels..."
echo ""

# Try ngrok first (if configured)
if command -v ngrok >/dev/null 2>&1; then
    echo "🔗 Trying ngrok..."
    timeout 10s ngrok http 8501 --log=stdout 2>&1 | grep -o 'https://[^[:space:]]*\.ngrok[^[:space:]]*' | head -1 &
    NGROK_PID=$!
    sleep 5
    
    # Check if ngrok worked
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('tunnels') and len(data['tunnels']) > 0:
        print(data['tunnels'][0]['public_url'])
except:
    pass
" 2>/dev/null)
    
    if [ ! -z "$NGROK_URL" ]; then
        echo "✅ ngrok tunnel: $NGROK_URL"
    else
        echo "⚠️  ngrok needs authentication. Visit: https://ngrok.com"
        pkill -f ngrok 2>/dev/null
    fi
else
    echo "⚠️  ngrok not available"
fi

echo ""
echo "🔗 Trying alternative tunnel (bore)..."

# Try bore.pub (a free alternative)
if command -v bore >/dev/null 2>&1; then
    bore local 8501 --to bore.pub &
    BORE_PID=$!
    echo "✅ bore tunnel: https://localhost-8501.bore.pub"
else
    echo "📦 Installing bore..."
    if command -v cargo >/dev/null 2>&1; then
        cargo install bore-cli
        bore local 8501 --to bore.pub &
        BORE_PID=$!
        echo "✅ bore tunnel: https://localhost-8501.bore.pub"
    else
        echo "⚠️  cargo not available for bore installation"
    fi
fi

echo ""
echo "📋 SUMMARY"
echo "=========="
echo "✅ Your VCT Dashboard is running!"
echo ""
echo "🏠 Local Access:"
echo "   http://localhost:8501"
echo ""
echo "🌐 Network Access (same WiFi):"
echo "   http://$LOCAL_IP:8501"
echo ""
echo "🌍 External Access:"
if [ ! -z "$NGROK_URL" ]; then
    echo "   $NGROK_URL"
else
    echo "   Set up ngrok: https://ngrok.com (free)"
fi
echo "   Try: https://localhost-8501.bore.pub (if bore is running)"
echo ""
echo "📱 Share any of these links with others!"
echo ""
echo "Press Ctrl+C to stop all services..."

# Keep script running and handle cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $STREAMLIT_PID 2>/dev/null
    pkill -f ngrok 2>/dev/null
    pkill -f bore 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

trap cleanup INT TERM

# Keep running
while true; do
    sleep 1
done
