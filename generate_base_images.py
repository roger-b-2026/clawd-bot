#!/usr/bin/env python3
"""
ComfyUI API Client for Base Image Generation
Reads prompts from character_prompts.md and generates base images
"""

import os
import json
import time
import requests
from pathlib import Path

# Configuration
COMFYUI_URL = "https://u0zzt223rri91k-8188.proxy.runpod.net"
PROMPT_FILE = Path(__file__).parent / "models" / "character_prompts.md"
OUTPUT_BASE = Path(__file__).parent / "models"


class ComfyUIAPI:
    """Simple ComfyUI API client"""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.client_id = "generate_images"
    
    def queue_prompt(self, workflow):
        """Queue a prompt for generation"""
        url = f"{self.base_url}/prompt"
        data = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def get_history(self, prompt_id):
        """Get generation history"""
        url = f"{self.base_url}/history/{prompt_id}"
        response = requests.get(url)
        return response.json()
    
    def download_image(self, filename, image_type="output"):
        """Download generated image"""
        url = f"{self.base_url}/view?filename={filename}&type={image_type}"
        response = requests.get(url)
        return response.content if response.status_code == 200 else None
    
    def generate(self, prompt_text, filename_prefix="base"):
        """Generate a single image with SDXL Base"""
        # Working SDXL workflow
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 7.0,
                    "denoise": 1.0,
                    "sampler_name": "euler_ancestral",
                    "scheduler": "normal",
                    "steps": 25,
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
                    "text": f"{prompt_text}, no face visible, neutral expression"
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": "ugly, deformed, noisy, blurry, low quality, bad anatomy, bad hands, extra fingers, fused fingers, poorly drawn face"
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
                    "filename_prefix": filename_prefix,
                    "images": ["9", 0]
                }
            }
        }
        
        # Queue the prompt
        result = self.queue_prompt(workflow)
        
        if "prompt_id" not in result:
            print(f"❌ Failed to queue: {result.get('error', 'Unknown error')}")
            return None
        
        prompt_id = result["prompt_id"]
        print(f"⏳ Generating: {filename_prefix}...")
        
        # Wait for completion (up to 120 seconds)
        for _ in range(60):
            time.sleep(2)
            try:
                history = self.get_history(prompt_id)
                if prompt_id in history:
                    status = history[prompt_id].get("status", {})
                    if status.get("status") == "success":
                        # Get output filename from history
                        outputs = history[prompt_id].get("outputs", {})
                        for node_id, output in outputs.items():
                            if "images" in output:
                                for img in output["images"]:
                                    if "filename" in img:
                                        return {
                                            "filename": img["filename"],
                                            "type": img.get("type", "output")
                                        }
            except Exception as e:
                print(f"  Warning: {e}")
        
        print(f"⚠️  Timeout: {filename_prefix}")
        return None


def parse_prompts_from_file(filepath):
    """Parse prompts from the markdown file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    prompts = []
    lines = content.split('\n')
    
    current_model = None
    current_category = None
    prompt_lines = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('# MODEL '):
            current_model = line.replace('# MODEL ', '').strip()
        elif line.startswith('## ') and 'prompts' in line.lower():
            if prompt_lines and current_model and current_category:
                prompts.append({
                    'model': current_model,
                    'category': current_category,
                    'prompt': '\n'.join(prompt_lines).strip()
                })
            current_category = line.replace('## ', '').split('(')[0].strip()
            prompt_lines = []
        elif line.startswith('### ') and current_category:
            if prompt_lines:
                prompts.append({
                    'model': current_model,
                    'category': current_category,
                    'prompt': '\n'.join(prompt_lines).strip()
                })
            prompt_lines = [line.replace('### ', '').strip()]
        elif line and not line.startswith('#') and not line.startswith('---'):
            prompt_lines.append(line)
    
    if prompt_lines and current_model and current_category:
        prompts.append({
            'model': current_model,
            'category': current_category,
            'prompt': '\n'.join(prompt_lines).strip()
        })
    
    return prompts


def generate_base_images():
    """Main function to generate all base images"""
    print("=" * 60)
    print("🎨 ComfyUI Base Image Generator")
    print("=" * 60)
    
    # Initialize API
    api = ComfyUIAPI(COMFYUI_URL)
    
    # Test connection
    try:
        r = requests.get(COMFYUI_URL)
        if r.status_code != 200:
            print(f"❌ ComfyUI not responding")
            return
        print(f"✅ Connected to ComfyUI")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Parse prompts
    if not PROMPT_FILE.exists():
        print(f"❌ Prompt file not found: {PROMPT_FILE}")
        return
    
    prompts = parse_prompts_from_file(PROMPT_FILE)
    print(f"📝 Found {len(prompts)} prompts")
    print(f"   Models: {set([p['model'] for p in prompts])}")
    
    # Generate images
    generated = 0
    failed = 0
    
    for i, prompt_data in enumerate(prompts):
        model = prompt_data['model'].replace(' ', '_').lower()
        category = prompt_data['category'].replace(' ', '_').lower()
        prompt = prompt_data['prompt']
        
        # Create output folder
        output_dir = OUTPUT_BASE / model / "poses" / "base" / category
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename_prefix = f"{model}_{category}_{i+1:02d}"
        
        print(f"\n[{i+1}/{len(prompts)}] {model}/{category}")
        
        # Generate image
        result = api.generate(prompt, filename_prefix)
        
        if result:
            # Download image
            img_data = api.download_image(result["filename"], result["type"])
            if img_data:
                save_path = output_dir / f"{filename_prefix}.png"
                with open(save_path, 'wb') as f:
                    f.write(img_data)
                print(f"   ✅ Saved: {save_path}")
                generated += 1
            else:
                print(f"   ⚠️  Download failed")
                failed += 1
        else:
            failed += 1
        
        # Rate limiting
        time.sleep(3)
    
    print("\n" + "=" * 60)
    print(f"✅ Complete: {generated}/{len(prompts)} generated, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    generate_base_images()
