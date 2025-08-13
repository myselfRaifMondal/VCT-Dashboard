#!/usr/bin/env python3
"""
🚀 VCT Dashboard Launcher
========================
Complete solution for running your VCT Dashboard with external access.
"""

import subprocess
import time
import socket
import sys
import signal
import webbrowser
import threading
from pathlib import Path

class VCTDashboardLauncher:
    def __init__(self):
        self.streamlit_process = None
        self.running = True
    
    def get_local_ip(self):
        """Get local network IP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
    
    def check_port_available(self, port):
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', port))
                return result != 0
        except:
            return False
    
    def start_streamlit(self):
        """Start the Streamlit application"""
        print("🎯 Starting VCT Dashboard...")
        
        try:
            # Start Streamlit with external access enabled
            self.streamlit_process = subprocess.Popen([
                "streamlit", "run", "app.py",
                "--server.address", "0.0.0.0", 
                "--server.port", "8501",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ])
            
            # Wait for startup
            print("⏳ Waiting for dashboard to start...")
            for i in range(10):
                if not self.check_port_available(8501):
                    print("✅ Dashboard is running!")
                    return True
                time.sleep(1)
            
            print("❌ Dashboard failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
            return False
    
    def open_browser(self):
        """Open browser to the dashboard"""
        try:
            webbrowser.open('http://localhost:8501')
            print("🌐 Opening dashboard in your browser...")
        except:
            print("🌐 Open http://localhost:8501 in your browser")
    
    def cleanup(self, signum=None, frame=None):
        """Clean up processes"""
        print("\\n🛑 Shutting down dashboard...")
        self.running = False
        
        if self.streamlit_process:
            self.streamlit_process.terminate()
            try:
                self.streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
        
        print("✅ Dashboard stopped")
        sys.exit(0)
    
    def display_access_info(self, local_ip):
        """Display all access methods"""
        print("\\n" + "="*60)
        print("🎊 VCT DASHBOARD IS RUNNING!")
        print("="*60)
        print()
        print("📱 ACCESS YOUR DASHBOARD:")
        print("─" * 30)
        print(f"🏠 Local:           http://localhost:8501")
        print(f"🌐 Network:         http://{local_ip}:8501")
        print()
        print("🌍 EXTERNAL ACCESS OPTIONS:")
        print("─" * 30)
        print("1️⃣  ngrok (Recommended):")
        print("   • Sign up: https://ngrok.com (free)")
        print("   • Get token: https://dashboard.ngrok.com/get-started/your-authtoken")
        print("   • Run: ngrok config add-authtoken YOUR_TOKEN")
        print("   • Run: ngrok http 8501")
        print()
        print("2️⃣  CloudFlare Tunnel:")
        print("   • Install: brew install cloudflared")
        print("   • Run: cloudflared tunnel --url http://localhost:8501")
        print()
        print("3️⃣  VS Code Port Forwarding:")
        print("   • Open in VS Code")
        print("   • Use 'Remote-Tunnels' extension")
        print("   • Forward port 8501")
        print()
        print("4️⃣  Share on same WiFi:")
        print(f"   • Anyone on your WiFi can use: http://{local_ip}:8501")
        print()
        print("=" * 60)
        print("💡 TIP: For external access, ngrok is the easiest!")
        print("⏹  Press Ctrl+C to stop the dashboard")
        print("=" * 60)
    
    def run(self):
        """Main launcher function"""
        # Handle shutdown signals
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        print("🚀 VCT Dashboard Launcher")
        print("=" * 25)
        
        # Get network info
        local_ip = self.get_local_ip()
        print(f"📍 Local IP: {local_ip}")
        
        # Start the dashboard
        if not self.start_streamlit():
            print("❌ Failed to start dashboard. Please check for errors.")
            return
        
        # Open browser after a short delay
        threading.Timer(2.0, self.open_browser).start()
        
        # Display access information
        self.display_access_info(local_ip)
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    launcher = VCTDashboardLauncher()
    launcher.run()
