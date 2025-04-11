from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import urlparse, parse_qs
import json

injected_server = None

def default_hook():
    print("default hook")

class InjectedServerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global injected_server
        parsed = urlparse(self.path)
        if parsed.path == "/generate":
            params = parse_qs(parsed.query)
            params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            print("Query parameters:", params)  # {'foo': ['bar'], 'x': ['1']}

            result = injected_server.hook(params) == True  # pass params to your hook

            self.send_response(200 if result else 500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = {
                "success": result,
                "params": params
            }

            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        return  # suppress logging to console

class InjectedServer:
    def __init__(self, hook=default_hook, host='127.0.0.1', port=5001):
        global injected_server
        self.hook = hook  # assign user hook
        self.server = HTTPServer((host, port), InjectedServerRequestHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.host = host
        self.port = port
        injected_server = self
        self.start()

    def start(self):
        print(f"Injected server running on {self.host}:{self.port}")
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        print("Injected server stopped")