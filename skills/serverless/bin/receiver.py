#!/usr/bin/env python3
"""
RunPod Command Receiver - Execute commands via HTTP
Deploy on RunPod: python3 receiver.py
Then trigger from anywhere with curl
"""
import os, subprocess, json, sys, time
from http.server import HTTPServer, BaseHTTPRequestHandler

API_KEY = os.environ.get("API_KEY", "clawdbot2026")
PORT = int(os.environ.get("PORT", 8888))

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/exec":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            
            try:
                data = json.loads(body)
                if data.get("key") != API_KEY:
                    self.send_response(401)
                    self.end_headers()
                    return
                
                cmd = data.get("command", "")
                cwd = data.get("cwd", "/workspace/runpod-slim/ComfyUI")
                
                print(f"Executing: {cmd}")
                
                result = subprocess.run(
                    cmd, shell=True, cwd=cwd,
                    capture_output=True, text=True, timeout=600
                )
                
                response = {
                    "status": "completed" if result.returncode == 0 else "failed",
                    "stdout": result.stdout[-10000:],  # Limit output
                    "stderr": result.stderr[-2000:],
                    "returncode": result.returncode
                }
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                error_resp = {"error": str(e)}
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps(error_resp).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[receiver] {args[0]}")

def main():
    # Generate command to run receiver
    start_cmd = f"nohup python3 {os.path.abspath(__file__)} > /tmp/receiver.log 2>&1 &"
    print(f"Starting receiver on port {PORT}...")
    print(f"To start in background: {start_cmd}")
    print(f"To stop: pkill -f receiver.py")
    print()
    print("Trigger example:")
    print(f'''curl -X POST http://localhost:{PORT}/exec \\
  -H "Content-Type: application/json" \\
  -d '{{"key":"{API_KEY}","command":"python3 /tmp/gen.py"}}' ''')
    
    # Actually start serving if not just showing help
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        server = HTTPServer(("", PORT), Handler)
        print(f"\n🚀 Listening on port {PORT}")
        server.serve_forever()

if __name__ == "__main__":
    if "--serve" in sys.argv:
        main()
    else:
        main()
