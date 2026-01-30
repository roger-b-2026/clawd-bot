#!/usr/bin/env python3
"""
Memory-optimized ComfyUI generator for RTX 4090 with limited VRAM
"""

import requests
import time
import os
from pathlib import Path

COMFYUI_URL = "https://u0zzt223rri91k-8188.proxy.runpod.net"
OUTPUT_DIR = Path("/Users/rogerb/clawd/models")

def generate_image(prompt, filename, category, model_name):
    """Generate a single image with memory-efficient settings"""
    
    # Memory-optimized SDXL workflow
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 5.0,  # Lower CFG saves memory
                "denoise": 1.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "steps": 15,  # Fewer steps
                "seed": 42,
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "latent_image": ["10", 0]
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "DreamShaper_8.safetensors"
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": f"{prompt}, no face visible, neutral expression, high quality"
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": "ugly, deformed, noisy, blurry, low quality, bad anatomy, extra fingers"
            }
        },
        "10": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "batch_size": 1,
                "height": 768,
                "width": 768
            }
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["10", 0],
                "vae": ["4", 2]
            }
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            }
        },
        "11": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename,
                "images": ["9", 0]
            }
        }
    }
    
    # Queue prompt
    r = requests.post(f"{COMFYUI_URL}/prompt", json={
        "client_id": "generator",
        "prompt": workflow
    })
    
    if r.status_code != 200:
        print(f"❌ Failed to queue: {r.text[:200]}")
        return False
    
    prompt_id = r.json()["prompt_id"]
    print(f"⏳ {filename}...")
    
    # Wait for completion (max 120 seconds)
    for _ in range(40):
        time.sleep(3)
        
        # Check queue
        q = requests.get(f"{COMFYUI_URL}/queue").json()
        if not q.get("queue_running") and not q.get("queue_pending"):
            # Check history for result
            h = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
            if prompt_id in h:
                status = h[prompt_id].get("status", {})
                if status.get("status") == "success":
                    outputs = h[prompt_id].get("outputs", {})
                    for node_id, output in outputs.items():
                        if "images" in output:
                            for img in output["images"]:
                                if "filename" in img:
                                    # Download image
                                    img_r = requests.get(
                                        f"{COMFYUI_URL}/view?filename={img['filename']}&type=output"
                                    )
                                    if img_r.status_code == 200:
                                        # Save to correct folder
                                        save_dir = OUTPUT_DIR / model_name / "poses" / "base" / category
                                        save_dir.mkdir(parents=True, exist_ok=True)
                                        save_path = save_dir / f"{filename}.png"
                                        with open(save_path, "wb") as f:
                                            f.write(img_r.content)
                                        print(f"✅ Saved: {save_path}")
                                        return True
                elif status.get("status") == "error":
                    print(f"❌ Error: {status.get('exception_message', 'Unknown')[:100]}")
                    return False
    
    print(f"⚠️  Timeout")
    return False


def main():
    print("=" * 60)
    print("🎨 Memory-Optimized Base Image Generator")
    print("=" * 60)
    
    # Test connection
    if requests.get(COMFYUI_URL).status_code != 200:
        print("❌ ComfyUI not responding")
        return
    
    print("✅ Connected to ComfyUI")
    
    # Read prompts
    prompt_file = Path("/Users/rogerb/clawd/models/character_prompts.md")
    with open(prompt_file) as f:
        content = f.read()
    
    # Parse prompts (simplified)
    prompts = []
    lines = content.split('\n')
    current_model = None
    current_category = None
    current_prompt = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('# MODEL '):
            current_model = line.replace('# MODEL ', '').strip()
        elif line.startswith('## ') and 'prompts' in line.lower():
            if current_prompt and current_model and current_category:
                prompts.append({
                    'model': current_model,
                    'category': line.replace('## ', '').split('(')[0].strip(),
                    'prompt': ' '.join(current_prompt)
                })
            current_category = line.replace('## ', '').split('(')[0].strip()
            current_prompt = []
        elif line.startswith('### ') and current_category:
            if current_prompt:
                prompts.append({
                    'model': current_model,
                    'category': current_category,
                    'prompt': ' '.join(current_prompt)
                })
            current_prompt = [line.replace('### ', '').strip()]
        elif line and not line.startswith('#') and not line.startswith('---'):
            current_prompt.append(line)
    
    if current_prompt:
        prompts.append({
            'model': current_model,
            'category': current_category,
            'prompt': ' '.join(current_prompt)
        })
    
    print(f"📝 Found {len(prompts)} prompts")
    
    # Generate images
    generated = 0
    failed = 0
    
    for i, p in enumerate(prompts):
        model_folder = p['model'].replace(' ', '_').lower().split(':')[-1].strip()
        category_folder = p['category'].replace(' ', '_').lower().split('-')[-1].strip()
        filename = f"{model_folder}_{category_folder}_{i+1:02d}"
        
        success = generate_image(p['prompt'], filename, category_folder, model_folder)
        
        if success:
            generated += 1
        else:
            failed += 1
        
        time.sleep(2)  # Rate limiting
    
    print(f"\n{'=' * 60}")
    print(f"✅ Complete: {generated} generated, {failed} failed")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
