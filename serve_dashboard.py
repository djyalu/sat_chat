#!/usr/bin/env python3
"""Simple HTTP server for SatChat Multi-Analysis Dashboard"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve multi_analysis.html as the main dashboard
        if self.path == '/' or self.path == '/multi_analysis.html':
            self.path = '/multi_analysis.html'
        elif self.path == '/real_data.html':
            self.path = '/real_data.html'
        elif self.path == '/index.html':
            self.path = '/index.html'
        
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def start_dashboard_server():
    PORT = 5555
    
    # Set the directory to serve files from
    os.chdir('/mnt/d/projects/sat_chat')
    
    print("🔬 Starting SatChat Multi-Analysis Dashboard Server...")
    print(f"📊 Dashboard URL: http://localhost:{PORT}")
    print(f"🛰️ Real Data URL: http://localhost:{PORT}/real_data.html")
    print(f"🏠 Main Index URL: http://localhost:{PORT}/index.html")
    print()
    print("Available APIs:")
    print("✅ Enhanced API (port 8003): python enhanced_api.py")
    print("📡 Real Sentinel API (port 8002): python real_sentinel_api.py")
    print()
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 Serving dashboard at http://localhost:{PORT}")
        
        # Try to open browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}')
            print("🌐 Browser opened automatically")
        except:
            print("💡 Please open http://localhost:5555 in your browser")
        
        print("\n📋 Dashboard Features:")
        print("  🔬 Multi-Index Analysis (FDI, NDWI, MCI, Turbidity)")
        print("  🤖 ML-Based Segmentation (23-class MARIDA)")
        print("  🗺️ Interactive Tile Maps")
        print("  ✅ Field Validation System")
        print("  🔄 Batch Processing")
        print("  📊 Real-time Statistics")
        print()
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Dashboard server stopped")

if __name__ == "__main__":
    start_dashboard_server()