from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'ok')

def run_server():
    server_address = ('', 80)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    httpd.serve_forever()

def start_web_server():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()