#!/usr/bin/env python3
"""
RunPod Command Receiver - Execute commands via HTTP
Deploy on RunPod: python3 receiver.py
Then trigger from anywhere with curl
"""
import os, subprocess, json, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

API_KEY = os.environ.get("API_KEY", "secret123")

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
                
                result = subprocess.run(
                    cmd, shell=True, cwd=cwd,
                    capture_output=True, text=True, timeout=300
                )
                
                response = {
                    "status": "completed" if result.returncode == 0 else "failed",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[receiver] {args[0]}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8888))
    print(f"🚀 RunPod Command Receiver listening on port {port}")
    print(f"   API_KEY: {API_KEY}")
    server = HTTPServer(("", port), Handler)
    server.serve_forever()
