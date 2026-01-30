#!/usr/bin/env python3
"""
RunPod Serverless Execution Tool
Executes Python scripts on serverless GPU instances
"""
import os, sys, json, time, requests, tempfile

API_KEY = os.environ.get("RUNPOD_API_KEY", "os.environ.get("RUNPOD_API_KEY", "")")
BASE_URL = "https://api.runpod.io/v1"

def headers():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def run_script_url(script_url):
    """Run a Python script from URL on serverless GPU"""
    
    # Create a job to run the script
    payload = {
        "input": {"url": script_url},
        "containerImage": "python:3.10-slim",
        "env": [{"key": "PYTHONUNBUFFERED", "value": "1"}],
        "timeout": 300
    }
    
    # Submit job
    resp = requests.post(
        f"{BASE_URL}/serverless/jobs",
        headers=headers(),
        json={"podType": "NVIDIA_T4", "cloudType": "SECURE", **payload}
    )
    
    if resp.status_code == 200:
        job_data = resp.json()
        job_id = job_data.get("id")
        print(f"Job submitted: {job_id}")
        
        # Poll for completion
        status_url = f"{BASE_URL}/serverless/jobs/status/{job_id}"
        for _ in range(60):  # 5 min max
            time.sleep(5)
            status_resp = requests.get(status_url, headers=headers())
            status = status_resp.json()
            print(f"Status: {status.get('status', 'unknown')}")
            
            if status.get("status") == "COMPLETED":
                print("\n=== OUTPUT ===")
                print(status.get("output", {}).get("result", "No output"))
                return status
            elif status.get("status") in ["FAILED", "TIMED_OUT", "CANCELLED"]:
                print(f"Job failed: {status}")
                return status
        
        print("Job timed out")
        return {"status": "TIMED_OUT"}
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
        return {"status": "error", "details": resp.text}

def run_inline_script(script_content):
    """Execute inline Python code"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        result = run_script_url(f"file://{script_path}")
        return result
    finally:
        os.unlink(script_path)

def main():
    if len(sys.argv) < 2:
        print("Usage: serverless <command> [args]")
        print("  run <url>     - Run script from URL")
        print("  exec <code>   - Execute inline Python")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "run" and len(sys.argv) > 2:
        run_script_url(sys.argv[2])
    elif cmd == "exec":
        script = " ".join(sys.argv[2:])
        run_inline_script(script)
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
