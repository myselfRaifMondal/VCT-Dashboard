#!/usr/bin/env python3
"""
🚀 Reliable VCT Dashboard with CloudFlare Tunnel
===============================================
Robust solution with proper error handling and monitoring.
"""

import subprocess
import time
import socket
import sys
import signal
import threading
import re
import requests
from pathlib import Path

class ReliableVCTRunner:
    def __init__(self):
        self.streamlit_process = None
        self.tunnel_process = None
        self.tunnel_url = None
        self.running = True
        self.local_ip = self.get_local_ip()
    
    def get_local_ip(self):
        """Get local network IP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
    
    def test_local_connection(self, max_attempts=10):
        """Test if Streamlit is responding locally"""
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8501", timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    def start_streamlit(self):
        """Start Streamlit with comprehensive error handling"""
        print("🎯 Starting VCT Dashboard...")
        
        try:
            # Kill any existing streamlit processes
            subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
            time.sleep(2)
            
            # Start Streamlit
            self.streamlit_process = subprocess.Popen([
                "streamlit", "run", "app.py",
                "--server.address", "0.0.0.0",
                "--server.port", "8501", 
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
                "--server.fileWatcherType", "none"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            print("⏳ Waiting for dashboard to start...")
            
            # Wait for Streamlit to be ready
            if self.test_local_connection():
                print("✅ VCT Dashboard is running and responding!")
                return True
            else:
                print("❌ Dashboard failed to start properly")
                self.check_streamlit_logs()
                return False
                
        except Exception as e:
            print(f"❌ Error starting Streamlit: {e}")
            return False
    
    def check_streamlit_logs(self):
        """Check Streamlit logs for errors"""
        if self.streamlit_process:
            try:
                stdout, stderr = self.streamlit_process.communicate(timeout=1)
                if stderr:
                    print("📝 Streamlit errors:")
                    print(stderr.decode('utf-8')[-500:])  # Last 500 chars
            except subprocess.TimeoutExpired:
                pass
    
    def start_cloudflare_tunnel(self):
        """Start CloudFlare tunnel with better monitoring"""
        print("🔗 Starting CloudFlare tunnel...")
        
        try:
            # Kill any existing cloudflared processes
            subprocess.run(["pkill", "-f", "cloudflared"], capture_output=True)
            time.sleep(2)
            
            # Start CloudFlare tunnel with explicit configuration
            self.tunnel_process = subprocess.Popen([
                "cloudflared", "tunnel", 
                "--url", "http://localhost:8501",
                "--logfile", "/tmp/cloudflared.log"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            print("⏳ Establishing tunnel connection...")
            
            # Monitor output for tunnel URL
            tunnel_established = False
            for i in range(60):  # Wait up to 60 seconds
                if not self.tunnel_process.poll() is None:
                    print("❌ Tunnel process ended unexpectedly")
                    self.check_tunnel_logs()
                    return False
                
                # Read output line by line
                try:
                    line = self.tunnel_process.stdout.readline()
                    if line:
                        print(f"   📡 {line.strip()}")
                        
                        # Look for the tunnel URL
                        if "https://" in line and ".trycloudflare.com" in line:
                            url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                            if url_match:
                                self.tunnel_url = url_match.group(0)
                                print(f"✅ Tunnel established!")
                                print(f"🌍 External URL: {self.tunnel_url}")
                                tunnel_established = True
                                break
                        
                        # Also check for connection confirmation
                        if "Registered tunnel connection" in line:
                            print("✅ Tunnel connection registered!")
                            
                except Exception as e:
                    print(f"   Error reading tunnel output: {e}")
                
                time.sleep(1)
            
            if not tunnel_established and self.tunnel_process.poll() is None:
                print("⚠️ Tunnel process is running but URL not detected yet")
                print("💡 Check logs or wait a bit longer for URL to appear")
                return True
                
            return tunnel_established
            
        except Exception as e:
            print(f"❌ Error starting CloudFlare tunnel: {e}")
            return False
    
    def check_tunnel_logs(self):
        """Check tunnel logs for errors"""
        try:
            if Path("/tmp/cloudflared.log").exists():
                with open("/tmp/cloudflared.log", "r") as f:
                    logs = f.read()[-1000:]  # Last 1000 chars
                    print("📝 Tunnel logs:")
                    print(logs)
        except Exception as e:
            print(f"Could not read tunnel logs: {e}")
    
    def test_external_connection(self):
        """Test if external tunnel is working"""
        if not self.tunnel_url:
            return False
        
        try:
            print(f"🧪 Testing external connection: {self.tunnel_url}")
            response = requests.get(self.tunnel_url, timeout=10)
            if response.status_code == 200:
                print("✅ External tunnel is working!")
                return True
            else:
                print(f"⚠️ External tunnel returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ External tunnel test failed: {e}")
            return False
    
    def monitor_services(self):
        """Monitor both services continuously"""
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            
            # Check Streamlit
            if not self.test_local_connection(max_attempts=2):
                print("⚠️ Streamlit appears to be down, attempting restart...")
                if self.start_streamlit():
                    print("✅ Streamlit restarted successfully")
                else:
                    print("❌ Failed to restart Streamlit")
            
            # Check tunnel process
            if self.tunnel_process and self.tunnel_process.poll() is not None:
                print("⚠️ Tunnel process ended, attempting restart...")
                if self.start_cloudflare_tunnel():
                    print("✅ Tunnel restarted successfully")
                else:
                    print("❌ Failed to restart tunnel")
    
    def cleanup(self, signum=None, frame=None):
        """Clean shutdown"""
        print("\\n🛑 Shutting down services...")
        self.running = False
        
        if self.tunnel_process:
            print("   Stopping tunnel...")
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
        
        if self.streamlit_process:
            print("   Stopping dashboard...")
            self.streamlit_process.terminate()
            try:
                self.streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
        
        # Final cleanup
        subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
        subprocess.run(["pkill", "-f", "cloudflared"], capture_output=True)
        
        print("✅ All services stopped cleanly")
        sys.exit(0)
    
    def display_status(self):
        """Display current status and URLs"""
        print("\\n" + "="*80)
        print("🎊 VCT DASHBOARD STATUS")
        print("="*80)
        print()
        print("📊 DASHBOARD FEATURES:")
        print("   ✅ VCT Data 2021-2025 (5+ million rows)")
        print("   ✅ Agent statistics and pick rates") 
        print("   ✅ Match overviews and results")
        print("   ✅ Player performance analytics")
        print("   ✅ Interactive charts and visualizations")
        print()
        print("🌐 ACCESS URLS:")
        print(f"   🏠 Local:    http://localhost:8501")
        print(f"   🌐 Network:  http://{self.local_ip}:8501")
        if self.tunnel_url:
            print(f"   🌍 External: {self.tunnel_url}")
            print()
            print("🔥 SHARE THIS LINK WITH ANYONE:")
            print(f"   {self.tunnel_url}")
        else:
            print("   🌍 External: Setting up tunnel...")
        print()
        print("="*80)
        print("💡 The tunnel URL will remain active as long as this script runs")
        print("⏹  Press Ctrl+C to stop all services")
        print("="*80)
    
    def run(self):
        """Main execution function"""
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        print("🚀 Reliable VCT Dashboard with CloudFlare Tunnel")
        print("=" * 50)
        print(f"📍 Local IP: {self.local_ip}")
        print()
        
        # Start services
        if not self.start_streamlit():
            print("❌ Failed to start dashboard")
            return
        
        if not self.start_cloudflare_tunnel():
            print("⚠️ Tunnel startup had issues, but continuing...")
        
        # Test connections
        time.sleep(3)
        if self.tunnel_url:
            self.test_external_connection()
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
        monitor_thread.start()
        
        # Display status
        self.display_status()
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    runner = ReliableVCTRunner()
    runner.run()
