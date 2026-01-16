#!/usr/bin/env python3
"""
ChirpStack CSV Importer - Serveur local avec proxy
Usage: python server.py [port]
Puis ouvrir http://localhost:8000 (ou le port choisi)
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import sys
import os
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

class ProxyHandler(http.server.SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Grpc-Metadata-Authorization, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/proxy/'):
            self.proxy_request('GET')
        else:
            # Serve static files
            if self.path == '/':
                self.path = '/main.html'
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/proxy/'):
            self.proxy_request('POST')
        else:
            self.send_error(404)

    def do_PUT(self):
        if self.path.startswith('/proxy/'):
            self.proxy_request('PUT')
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith('/proxy/'):
            self.proxy_request('DELETE')
        else:
            self.send_error(404)

    def proxy_request(self, method):
        """Proxy requests to ChirpStack API"""
        try:
            # Parse the proxy URL: /proxy/{base64_url}/api/...
            # Format: /proxy/http://localhost:8090/api/tenants
            path_parts = self.path[7:]  # Remove '/proxy/'

            # Find the actual API path
            # URL format: /proxy/http://host:port/api/...
            if path_parts.startswith('http://') or path_parts.startswith('https://'):
                target_url = path_parts
            else:
                self.send_error(400, 'Invalid proxy URL format')
                return

            # Read request body for POST/PUT
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # Build the proxied request
            req = urllib.request.Request(target_url, data=body, method=method)

            # Forward relevant headers
            req.add_header('Accept', 'application/json')
            auth_header = self.headers.get('Grpc-Metadata-Authorization', '')
            if auth_header:
                req.add_header('Grpc-Metadata-Authorization', auth_header)
            if 'Content-Type' in self.headers:
                req.add_header('Content-Type', self.headers['Content-Type'])

            # Make the request
            with urllib.request.urlopen(req, timeout=30) as response:
                response_body = response.read()

                self.send_response(response.status)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', len(response_body))
                self.end_headers()
                self.wfile.write(response_body)

        except urllib.error.HTTPError as e:
            error_body = e.read()
            self.send_response(e.code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(error_body))
            self.end_headers()
            self.wfile.write(error_body)

        except urllib.error.URLError as e:
            error_msg = json.dumps({'error': str(e.reason)}).encode()
            self.send_response(502)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(error_msg))
            self.end_headers()
            self.wfile.write(error_msg)

        except Exception as e:
            error_msg = json.dumps({'error': str(e)}).encode()
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(error_msg))
            self.end_headers()
            self.wfile.write(error_msg)

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')

    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print("")
        print("=" * 50)
        print("  ChirpStack CSV Importer - Serveur Local")
        print("=" * 50)
        print(f"  Serveur demarre sur: http://localhost:{PORT}")
        print("")
        print("  Ouvrez cette URL dans votre navigateur")
        print("  Appuyez sur Ctrl+C pour arreter")
        print("=" * 50)
        print("")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrêté.")


if __name__ == '__main__':
    main()
