#!/usr/bin/env python3
"""
RunPod API Integration for Clawdbot
Execute commands on RunPod GPU instances
"""
import os, sys, json, urllib.request, urllib.error, subprocess

GRAPHQL_URL = "https://api.runpod.io/graphql"

class RunPodClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("RUNPOD_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "curl/7.68.0"
        }
    
    def _graphql(self, query, variables=None):
        data = {"query": query}
        if variables:
            data["variables"] = variables
        
        req = urllib.request.Request(
            GRAPHQL_URL,
            data=json.dumps(data).encode(),
            headers=self.headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"errors": [{"message": str(e)}]}
    
    def list_pods(self):
        result = self._graphql("{ myself { pods { id name podType desiredStatus } } }")
        return result.get("data", {}).get("myself", {}).get("pods", [])
    
    def exec_ssh(self, pod_id, command, cwd="/workspace/runpod-slim/ComfyUI"):
        full_cmd = f"cd {cwd} && {command}"
        
        ssh_cmd = [
            "ssh",
            "-i", "/Users/rogerb/.ssh/runpod_ed25519",
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            "-o", "RequestTTY=no",
            f"root@{pod_id}.pod.runpod.io",
            full_cmd
        ]
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout"}
        except Exception as e:
            return {"error": str(e)}

def generate_workflows():
    """Generate Cristie workflows on RunPod"""
    client = RunPodClient()
    pods = client.list_pods()
    
    if not pods:
        print("No pods found!")
        return False
    
    pod_id = pods[0]["id"]
    print(f"Running on pod {pod_id}...")
    
    cmd = 'curl -s https://raw.githubusercontent.com/roger-b-2026/main/scripts/generate_cristie_workflows.py -o /tmp/gen.py && python3 /tmp/gen.py'
    result = client.exec_ssh(pod_id, cmd)
    
    if result.get("status") == "completed":
        print("✓ Workflows generated!")
        print(result.get("stdout", ""))
        return True
    else:
        print(f"✗ Failed: {result}")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--gen":
        generate_workflows()
        return
    
    client = RunPodClient()
    pods = client.list_pods()
    
    print("=== RunPod Pods ===")
    for pod in pods:
        print(f"  {pod['id']} - {pod['name']} ({pod['podType']}) - {pod['desiredStatus']}")

if __name__ == "__main__":
    main()
