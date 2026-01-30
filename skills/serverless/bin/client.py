#!/usr/bin/env python3
"""
Remote Command Client - Trigger commands on RunPod
Usage: python3 client.py "curl https://..." --cwd /workspace/runpod-slim/ComfyUI
"""
import os, sys, json, requests, argparse

RUNPOD_HOST = os.environ.get("RUNPOD_HOST", "")
API_KEY = os.environ.get("API_KEY", "secret123")

def send_command(command, cwd="/workspace/runpod-slim/ComfyUI"):
    """Send command to RunPod receiver"""
    if not RUNPOD_HOST:
        print("Error: RUNPOD_HOST not set")
        print("Export RUNPOD_HOST=https://your-runpod-ip:8888")
        sys.exit(1)
    
    data = {"key": API_KEY, "command": command, "cwd": cwd}
    
    try:
        resp = requests.post(f"{RUNPOD_HOST}/exec", json=data, timeout=30)
        result = resp.json()
        
        print("=== STDOUT ===")
        print(result.get("stdout", ""))
        print("\n=== STDERR ===")
        print(result.get("stderr", ""))
        print(f"\nReturn code: {result.get('returncode')}")
        
        return result.get("returncode", 1)
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run command on RunPod")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--cwd", default="/workspace/runpod-slim/ComfyUI", help="Working directory")
    
    args = parser.parse_args()
    sys.exit(send_command(args.command, args.cwd))
