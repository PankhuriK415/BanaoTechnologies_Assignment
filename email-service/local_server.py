from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import os

# Append current directory to system path to import handler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from handler import send_email

class ServerlessOfflineSimulator(BaseHTTPRequestHandler):
    """
    HTTP Request Handler mimicking the Serverless Offline AWS Lambda local proxy gateway.
    Exposes the POST /dev/email/send endpoint.
    """
    def do_OPTIONS(self):
        # Enable CORS for local testing
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # Match standard serverless-offline paths
        if self.path in ['/dev/email/send', '/email/send']:
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Reconstruct AWS Lambda HTTP integration event
                event = {
                    'body': post_data
                }
                
                print(f"[Simulator] Invoking Lambda send_email with payload: {post_data}")
                
                # Invoke the serverless function handler directly
                result = send_email(event, None)
                
                # Send response
                self.send_response(result.get('statusCode', 200))
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(result.get('body', '{}').encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'Simulator execution crash: {str(e)}'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Route {self.path} not found'}).encode('utf-8'))

def run(port=3000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ServerlessOfflineSimulator)
    print(f"\n============================================================")
    print(f"Serverless offline simulator running on http://localhost:{port}/dev/email/send")
    print(f"Press Ctrl+C to terminate...")
    print(f"============================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Serverless offline simulator...")
    httpd.server_close()

if __name__ == '__main__':
    run()
