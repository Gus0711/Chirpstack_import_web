#!/usr/bin/env python3
"""
ChirpStack CSV Importer - Version Docker
Usage: python server.py [port]
Adaptations Docker:
  - Ecoute sur 0.0.0.0 (accessible depuis l'extérieur du container)
  - Stockage des données dans /app/data/ (volume persistant)
  - allow_reuse_address pour éviter les erreurs au redémarrage
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import sys
import os
import uuid
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Configuration
PORT = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 8000))
HOST = os.environ.get('HOST', '0.0.0.0')  # Docker: écoute sur toutes les interfaces
DATA_DIR = os.environ.get('DATA_DIR', '/app/data')

# Chemins des fichiers de données
PROFILES_FILE = os.path.join(DATA_DIR, 'profiles.json')
SERVERS_FILE = os.path.join(DATA_DIR, 'servers.json')


def ensure_data_dir():
    """Crée le dossier data si nécessaire"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"[INFO] Dossier de données créé: {DATA_DIR}")


def load_profiles():
    """Load profiles from JSON file"""
    if not os.path.exists(PROFILES_FILE):
        return {"profiles": []}
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"profiles": []}


def save_profiles(data):
    """Save profiles to JSON file"""
    ensure_data_dir()
    with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_servers():
    """Load servers from JSON file"""
    if not os.path.exists(SERVERS_FILE):
        return {"servers": []}
    try:
        with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"servers": []}


def save_servers(data):
    """Save servers to JSON file"""
    ensure_data_dir()
    with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
        elif self.path == '/api/profiles' or self.path.startswith('/api/profiles?'):
            self.handle_get_profiles()
        elif self.path == '/api/servers' or self.path.startswith('/api/servers?'):
            self.handle_get_servers()
        elif self.path == '/health':
            self.handle_health_check()
        else:
            # Serve static files
            if self.path == '/':
                self.path = '/main.html'
            super().do_GET()

    def handle_health_check(self):
        """Endpoint de health check pour Docker/Kubernetes"""
        response = json.dumps({'status': 'healthy', 'service': 'chirpstack-importer'}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def handle_get_profiles(self):
        """Return all profiles"""
        data = load_profiles()
        response = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def handle_get_servers(self):
        """Return all saved servers"""
        data = load_servers()
        response = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        if self.path.startswith('/proxy/'):
            self.proxy_request('POST')
        elif self.path == '/api/profiles':
            self.handle_create_profile()
        elif self.path == '/api/servers':
            self.handle_create_server()
        else:
            self.send_error(404)

    def handle_create_profile(self):
        """Create a new profile"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            profile_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json_error(400, 'Invalid JSON')
            return

        if not profile_data.get('name'):
            self.send_json_error(400, 'Profile name is required')
            return

        data = load_profiles()
        now = datetime.utcnow().isoformat() + 'Z'

        new_profile = {
            'id': str(uuid.uuid4()),
            'name': profile_data['name'],
            'requiredTags': profile_data.get('requiredTags', []),
            'createdAt': now,
            'updatedAt': now
        }

        data['profiles'].append(new_profile)
        save_profiles(data)

        response = json.dumps(new_profile).encode('utf-8')
        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def handle_create_server(self):
        """Create a new saved server"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            server_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json_error(400, 'Invalid JSON')
            return

        if not server_data.get('name') or not server_data.get('url'):
            self.send_json_error(400, 'Server name and URL are required')
            return

        data = load_servers()
        now = datetime.utcnow().isoformat() + 'Z'

        # Check if URL already exists
        for server in data['servers']:
            if server['url'] == server_data['url']:
                self.send_json_error(409, 'Server URL already exists')
                return

        new_server = {
            'id': str(uuid.uuid4()),
            'name': server_data['name'],
            'url': server_data['url'],
            'createdAt': now
        }

        data['servers'].append(new_server)
        save_servers(data)

        response = json.dumps(new_server).encode('utf-8')
        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def do_PUT(self):
        if self.path.startswith('/proxy/'):
            self.proxy_request('PUT')
        elif self.path.startswith('/api/profiles/'):
            self.handle_update_profile()
        else:
            self.send_error(404)

    def handle_update_profile(self):
        """Update an existing profile"""
        profile_id = self.path.split('/api/profiles/')[-1]

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            profile_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json_error(400, 'Invalid JSON')
            return

        data = load_profiles()
        profile_found = False

        for profile in data['profiles']:
            if profile['id'] == profile_id:
                profile['name'] = profile_data.get('name', profile['name'])
                profile['requiredTags'] = profile_data.get('requiredTags', profile['requiredTags'])
                profile['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
                profile_found = True

                save_profiles(data)
                response = json.dumps(profile).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(response))
                self.end_headers()
                self.wfile.write(response)
                break

        if not profile_found:
            self.send_json_error(404, 'Profile not found')

    def do_DELETE(self):
        if self.path.startswith('/proxy/'):
            self.proxy_request('DELETE')
        elif self.path.startswith('/api/profiles/'):
            self.handle_delete_profile()
        elif self.path.startswith('/api/servers/'):
            self.handle_delete_server()
        else:
            self.send_error(404)

    def handle_delete_profile(self):
        """Delete a profile"""
        profile_id = self.path.split('/api/profiles/')[-1]

        data = load_profiles()
        original_length = len(data['profiles'])
        data['profiles'] = [p for p in data['profiles'] if p['id'] != profile_id]

        if len(data['profiles']) == original_length:
            self.send_json_error(404, 'Profile not found')
            return

        save_profiles(data)
        response = json.dumps({'success': True}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def handle_delete_server(self):
        """Delete a saved server"""
        server_id = self.path.split('/api/servers/')[-1]

        data = load_servers()
        original_length = len(data['servers'])
        data['servers'] = [s for s in data['servers'] if s['id'] != server_id]

        if len(data['servers']) == original_length:
            self.send_json_error(404, 'Server not found')
            return

        save_servers(data)
        response = json.dumps({'success': True}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def send_json_error(self, code, message):
        """Send a JSON error response"""
        response = json.dumps({'error': message}).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

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


class ReusableTCPServer(socketserver.TCPServer):
    """TCPServer avec allow_reuse_address pour éviter les erreurs au redémarrage"""
    allow_reuse_address = True


def main():
    # Change to app directory for serving static files
    app_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    os.chdir(app_dir)

    # Ensure data directory exists
    ensure_data_dir()

    with ReusableTCPServer((HOST, PORT), ProxyHandler) as httpd:
        print("")
        print("=" * 50)
        print("  ChirpStack CSV Importer - Docker")
        print("=" * 50)
        print(f"  Serveur demarre sur: http://{HOST}:{PORT}")
        print(f"  Dossier de données: {DATA_DIR}")
        print("")
        print("  Health check: /health")
        print("  Appuyez sur Ctrl+C pour arreter")
        print("=" * 50)
        print("")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrêté.")


if __name__ == '__main__':
    main()
