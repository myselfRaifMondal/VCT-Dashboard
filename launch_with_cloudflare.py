#!/usr/bin/env python3
"""
🚀 VCT Dashboard with CloudFlare Tunnel
======================================
Complete solution with CloudFlare Tunnel for external access.
"""

import subprocess
import time
import socket
import sys
import signal
import webbrowser
import threading
import re
from pathlib import Path

class VCTCloudFlareRunner:
    def __init__(self):
        self.streamlit_process = None
        self.tunnel_process = None
        self.tunnel_url = None
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
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for startup
            print("⏳ Waiting for dashboard to start...")
            for i in range(15):
                if not self.check_port_available(8501):
                    print("✅ VCT Dashboard is running!")
                    return True
                time.sleep(1)
                print(f"   Still starting... ({i+1}/15)")
            
            print("❌ Dashboard failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
            return False
    
    def start_cloudflare_tunnel(self):
        """Start CloudFlare tunnel"""
        print("🔗 Starting CloudFlare tunnel...")
        
        try:
            # Start CloudFlare tunnel
            self.tunnel_process = subprocess.Popen([
                "cloudflared", "tunnel", "--url", "http://localhost:8501"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor the output to get the tunnel URL
            print("⏳ Establishing tunnel...")
            for i in range(30):  # Wait up to 30 seconds
                if self.tunnel_process.poll() is not None:
                    print("❌ Tunnel process ended unexpectedly")
                    return False
                
                # Try to read from both stdout and stderr
                try:
                    # Check stderr first (cloudflared usually outputs there)
                    line = self.tunnel_process.stderr.readline()
                    if line:
                        print(f"   Tunnel log: {line.strip()}")
                        # Look for the tunnel URL
                        if "https://" in line and ".trycloudflare.com" in line:
                            # Extract the URL using regex
                            url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                            if url_match:
                                self.tunnel_url = url_match.group(0)
                                print(f"✅ CloudFlare tunnel established!")
                                print(f"🌍 External URL: {self.tunnel_url}")
                                return True
                except:
                    pass
                
                time.sleep(1)
            
            print("⚠️ Could not detect tunnel URL, but tunnel might be working")
            return True
            
        except Exception as e:
            print(f"❌ Error starting CloudFlare tunnel: {e}")
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
        print("\\n🛑 Shutting down...")
        self.running = False
        
        if self.tunnel_process:
            print("   Stopping CloudFlare tunnel...")
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
        
        if self.streamlit_process:
            print("   Stopping VCT Dashboard...")
            self.streamlit_process.terminate()
            try:
                self.streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
        
        print("✅ All services stopped")
        sys.exit(0)
    
    def display_access_info(self, local_ip):
        """Display all access methods"""
        print("\\n" + "="*70)
        print("🎊 VCT DASHBOARD WITH CLOUDFLARE TUNNEL IS RUNNING!")
        print("="*70)
        print()
        print("📱 ACCESS YOUR DASHBOARD:")
        print("─" * 40)
        print(f"🏠 Local:           http://localhost:8501")
        print(f"🌐 Network:         http://{local_ip}:8501")
        
        if self.tunnel_url:
            print(f"🌍 External:        {self.tunnel_url}")
            print()
            print("🔥 SHARE THIS EXTERNAL LINK WITH ANYONE:")
            print(f"   {self.tunnel_url}")
        else:
            print("🌍 External:        Check tunnel logs above for URL")
            print()
            print("💡 TIP: Look for 'trycloudflare.com' URL in the logs above")
        
        print()
        print("✨ FEATURES:")
        print("─" * 15)
        print("✅ Complete VCT data (2021-2025)")
        print("✅ All match overviews, player stats, agent data")
        print("✅ Interactive charts and analytics")
        print("✅ Real-time updates")
        print("✅ External access via CloudFlare")
        print()
        print("="*70)
        print("⏹  Press Ctrl+C to stop everything")
        print("="*70)
    
    def monitor_processes(self):
        """Monitor both processes in background"""
        while self.running:
            time.sleep(5)
            
            # Check if streamlit is still running
            if self.streamlit_process and self.streamlit_process.poll() is not None:
                print("⚠️ Streamlit process ended unexpectedly")
                break
            
            # Check if tunnel is still running
            if self.tunnel_process and self.tunnel_process.poll() is not None:
                print("⚠️ CloudFlare tunnel ended unexpectedly")
                # Tunnel might restart itself, so don't break immediately
    
    def run(self):
        """Main launcher function"""
        # Handle shutdown signals
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        print("🚀 VCT Dashboard with CloudFlare Tunnel")
        print("=" * 40)
        
        # Get network info
        local_ip = self.get_local_ip()
        print(f"📍 Local IP: {local_ip}")
        print()
        
        # Start the dashboard
        if not self.start_streamlit():
            print("❌ Failed to start dashboard. Please check for errors.")
            return
        
        # Start CloudFlare tunnel
        if not self.start_cloudflare_tunnel():
            print("❌ Failed to start CloudFlare tunnel")
            print("💡 Dashboard is still available locally at http://localhost:8501")
        
        # Open browser after a short delay
        threading.Timer(3.0, self.open_browser).start()
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Display access information
        self.display_access_info(local_ip)
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    runner = VCTCloudFlareRunner()
    runner.run()
