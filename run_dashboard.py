#!/usr/bin/env python3
"""
VCT Dashboard - External Access Runner
====================================
This script runs your VCT Dashboard with both local and external access options.
"""

import subprocess
import threading
import time
import signal
import sys
import socket
import requests
from pathlib import Path

class DashboardRunner:
    def __init__(self):
        self.streamlit_process = None
        self.tunnel_process = None
        self.running = True
        
    def get_local_ip(self):
        """Get the local network IP address"""
        try:
            # Connect to a remote address to determine the local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "localhost"
    
    def check_streamlit_running(self, max_attempts=10):
        """Check if Streamlit is running on port 8501"""
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8501", timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    def start_streamlit(self):
        """Start Streamlit app"""
        print("🎯 Starting VCT Dashboard...")
        try:
            self.streamlit_process = subprocess.Popen([
                "streamlit", "run", "app.py",
                "--server.address", "0.0.0.0",
                "--server.port", "8501",
                "--server.headless", "true"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if self.check_streamlit_running():
                return True
            else:
                print("❌ Failed to start Streamlit")
                return False
        except Exception as e:
            print(f"❌ Error starting Streamlit: {e}")
            return False
    
    def try_ngrok_tunnel(self):
        """Try to create ngrok tunnel"""
        try:
            from pyngrok import ngrok, conf
            
            # Kill any existing ngrok processes
            try:
                ngrok.kill()
            except:
                pass
            
            print("🔗 Creating ngrok tunnel...")
            
            # Create tunnel
            public_tunnel = ngrok.connect(8501)
            public_url = public_tunnel.public_url
            
            print(f"✅ ngrok tunnel: {public_url}")
            return public_url
            
        except Exception as e:
            if "authtoken" in str(e).lower():
                print("⚠️  ngrok requires authentication:")
                print("   1. Sign up at https://ngrok.com (free)")
                print("   2. Get your authtoken")  
                print("   3. Run: ngrok config add-authtoken YOUR_TOKEN")
            else:
                print(f"⚠️  ngrok failed: {e}")
            return None
    
    def try_serveo_tunnel(self):
        """Try to create serveo.net tunnel"""
        try:
            print("🔗 Creating serveo tunnel...")
            
            # Start serveo tunnel in background
            self.tunnel_process = subprocess.Popen([
                "ssh", "-o", "StrictHostKeyChecking=no", 
                "-R", "80:localhost:8501", "serveo.net"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it time to establish
            time.sleep(3)
            
            if self.tunnel_process.poll() is None:  # Still running
                print("✅ serveo tunnel: https://serveo.net (check terminal for URL)")
                return "https://serveo.net"
            else:
                print("⚠️  serveo tunnel failed")
                return None
                
        except Exception as e:
            print(f"⚠️  serveo failed: {e}")
            return None
    
    def cleanup(self, signum=None, frame=None):
        """Clean up all processes"""
        print("\n🛑 Shutting down...")
        self.running = False
        
        if self.streamlit_process:
            self.streamlit_process.terminate()
            
        if self.tunnel_process:
            self.tunnel_process.terminate()
        
        # Kill any remaining processes
        try:
            subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
            subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
        except:
            pass
        
        print("✅ All services stopped")
        sys.exit(0)
    
    def run(self):
        """Main runner function"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        print("🚀 VCT Dashboard - External Access Setup")
        print("=" * 50)
        
        local_ip = self.get_local_ip()
        print(f"📍 Local Network IP: {local_ip}")
        print()
        
        # Start Streamlit
        if not self.start_streamlit():
            return
        
        print("✅ VCT Dashboard is running!")
        print()
        print("🌐 Access URLs:")
        print(f"   Local:        http://localhost:8501")
        print(f"   Network:      http://{local_ip}:8501")
        print()
        
        # Try external tunnels
        print("🌍 Setting up external access...")
        external_urls = []
        
        # Try ngrok first
        ngrok_url = self.try_ngrok_tunnel()
        if ngrok_url:
            external_urls.append(ngrok_url)
        
        # Try serveo as backup
        if not external_urls:
            serveo_url = self.try_serveo_tunnel()
            if serveo_url:
                external_urls.append(serveo_url)
        
        print()
        print("📋 FINAL SUMMARY")
        print("=" * 20)
        print("✅ Your VCT Dashboard is running!")
        print()
        print("🏠 Local Access:")
        print(f"   http://localhost:8501")
        print()
        print("🌐 Network Access (same WiFi):")
        print(f"   http://{local_ip}:8501")
        print()
        print("🌍 External Access:")
        if external_urls:
            for url in external_urls:
                print(f"   {url}")
        else:
            print("   Setup ngrok for external access: https://ngrok.com")
        print()
        print("📱 Share these links with others!")
        print("⏹  Press Ctrl+C to stop...")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    runner = DashboardRunner()
    runner.run()
