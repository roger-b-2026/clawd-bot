#!/usr/bin/env python3
"""
RunPod Serverless Function - Executes Python on GPU
Deploy this as a serverless endpoint
"""
import json, os, subprocess, tempfile

def handler(event):
    """Handle execution requests"""
    
    script_url = event.get("input", {}).get("script_url")
    inline_code = event.get("input", {}).get("code")
    
    if script_url:
        # Fetch and run script from URL
        import requests
        response = requests.get(script_url)
        code = response.text
    elif inline_code:
        code = inline_code
    else:
        return {"error": "No script_url or code provided"}
    
    # Execute in temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        script_path = f.name
    
    try:
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "status": "completed",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    finally:
        os.unlink(script_path)

# Local testing
if __name__ == "__main__":
    test_event = {"input": {"code": "print('Hello from GPU!')"}}
    print(handler(test_event))
