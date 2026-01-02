#!/usr/bin/env python3
"""
Simple HTTP server for Risk Runners website
Serves the static website with proper CORS headers
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers for local development"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        # Aggressive cache control for development
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        
        # Extra cache busting for JavaScript and JSON files
        if self.path.endswith(('.js', '.json')):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0, s-maxage=0')
            self.send_header('ETag', f'"{hash(self.path + str(os.path.getmtime(self.translate_path(self.path)) if os.path.exists(self.translate_path(self.path)) else 0))}"')
        
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.address_string()}] {format % args}")

def main():
    # Change to the website directory
    website_dir = Path(__file__).parent
    os.chdir(website_dir)
    
    # Default port
    port = 8000
    
    # Check if port is specified as command line argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    # Find an available port if the default is taken
    while True:
        try:
            with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
                print(f"\n🚀 Risk Runners website server starting...")
                print(f"📁 Serving directory: {website_dir.absolute()}")
                print(f"🌐 Server running at: http://localhost:{port}")
                print(f"📱 Also available at: http://127.0.0.1:{port}")
                print(f"\n🔗 Quick links:")
                print(f"   • Main site: http://localhost:{port}")
                print(f"   • Industry browser: http://localhost:{port}/companies/by-industry.html")
                print(f"   • Company directory: http://localhost:{port}/companies/directory.html")
                print(f"\n💡 Press Ctrl+C to stop the server")
                print("-" * 60)
                
                httpd.serve_forever()
                
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"Port {port} is already in use, trying {port + 1}...")
                port += 1
                if port > 8010:  # Prevent infinite loop
                    print("Could not find an available port between 8000-8010")
                    sys.exit(1)
            else:
                print(f"Error starting server: {e}")
                sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n👋 Server stopped. Thanks for using Risk Runners!")
        sys.exit(0)