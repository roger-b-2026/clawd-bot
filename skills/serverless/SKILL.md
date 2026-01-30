# serverless Skill

Execute Python scripts on serverless GPU instances (RunPod).

## Commands

### Deploy & Run
```bash
# Run a Python script from a URL
clawdbot serverless run https://example.com/script.py

# Run inline Python
clawdbot serverless exec "print('hello from GPU')"

# Run from local file
clawdbot serverless run /path/to/script.py
```

### Manage Functions
```bash
# List deployed functions
clawdbot serverless list

# Remove a function
clawdbot serverless remove function_name
```

## Configuration

Set your RunPod API token:
```bash
export RUNPOD_API_KEY="rpa_..."
```

Or configure in Clawdbot settings.

## Example Use Cases

- Generate ComfyUI workflows
- Batch process images
- Run AI inference
- Any GPU-accelerated Python task
