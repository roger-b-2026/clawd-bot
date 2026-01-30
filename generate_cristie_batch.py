#!/usr/bin/env python3
"""
Cristie Desouza - Automated Prompt Generator & Batch Runner
Reads prompts from character_prompts_detailed.md and generates images via ComfyUI API
"""

import json
import os
import time
import re
from pathlib import Path

# Configuration
PROMPTS_FILE = "/workspace/runpod-slim/ComfyUI/models/cristie_desouza/character_prompts_detailed.md"
OUTPUT_DIR = "/workspace/runpod-slim/ComfyUI/output/cristie_desouza"
WORKFLOW_DIR = "/workspace/runpod-slim/ComfyUI/user/default/workflows"

# Quality tags (same for all prompts)
QUALITY_TAGS = "photorealistic, hyperrealistic, 8k uhd, dslr quality, sharp focus, professional photography, Canon EOS 5D Mark IV, 85mm lens, f/2.8, natural skin texture, detailed pores, realistic eyes, individual hair strands, fabric texture, cinematic lighting, warm color grading"

# Negative prompt
NEGATIVE_PROMPT = "cartoon, anime, illustration, painting, drawing, artificial, plastic skin, airbrushed, smooth skin, mannequin, doll-like, cgi, 3d render, overexposed, undersaturated, blurry, low quality, bad anatomy, extra limbs, distorted face, ugly eyes, deformed hands, bad fingers, watermark, text, cropped, frame, border, duplicate, mutation, poorly drawn face, poorly drawn hands, missing fingers, extra digits, fewer digits, signature, username, artist name, style, meme, low contrast, washed out, oversaturated, grainy, noisy, dithering, aliasing, jagged edges, halos, artifacts, compression artifacts"

# Physical description (constant across all prompts)
PHYSICAL_DESC = "28 year old Latina woman, 5'7\", toned athletic yet curvy feminine physique, tanned skin with golden undertones, long dark brunette hair with subtle sun-kissed highlights and natural beach waves, striking emerald green eyes, high cheekbones, full lips in warm smile, visible subtle shoulder freckles, UK dress size 10, 32DD bust, confident warm presence"

def parse_prompts_file(filepath):
    """Parse the prompts markdown file and extract all prompts"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    prompts = []
    
    # Split by prompt sections
    sections = re.split(r'### \d+\.', content)
    
    for i, section in enumerate(sections[1:], 1):  # Skip first empty section
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Extract title and prompt
        title_line = lines[0].strip()
        prompt_text = ' '.join(lines[1:]).strip()
        
        # Determine lane from title
        title_lower = title_line.lower()
        if 'sfw' in title_lower:
            lane = 'SFW'
        elif 'suggestive' in title_lower:
            lane = 'SUGGESTIVE'
        elif 'spicy' in title_lower:
            lane = 'SPICY'
        elif 'nsfw' in title_lower:
            lane = 'NSFW'
        else:
            lane = 'UNKNOWN'
        
        # Extract category
        if 'standing' in title_lower:
            category = 'STANDING'
        elif 'seated' in title_lower:
            category = 'SEATED'
        elif 'reclining' in title_lower:
            category = 'RECLINING'
        elif 'action' in title_lower:
            category = 'ACTION'
        else:
            category = 'UNKNOWN'
        
        # Generate safe filename
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title_line)[:50]
        filename = f"cristie_{lane}_{category}_{safe_title}.png"
        
        prompts.append({
            'title': title_line,
            'prompt': prompt_text,
            'lane': lane,
            'category': category,
            'filename': filename
        })
    
    return prompts

def generate_workflow_json(prompt, output_filename):
    """Generate a ComfyUI workflow JSON for this prompt"""
    
    workflow = {
        "last_node_id": 15,
        "last_link_id": 30,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [0, 400],
                "size": [320, 100],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [2, 3], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [4], "slot_index": 2}
                ],
                "widgets_values": ["Juggernaut-XL.safetensors"]
            },
            {
                "id": 2,
                "type": "CLIPTextEncode",
                "pos": [350, 50],
                "size": [420, 150],
                "inputs": [{"name": "clip", "type": "CLIP", "links": [2], "slot_index": 0}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [5, 6, 20], "slot_index": 0}],
                "widgets_values": [prompt]
            },
            {
                "id": 3,
                "type": "CLIPTextEncode",
                "pos": [350, 250],
                "size": [420, 150],
                "inputs": [{"name": "clip", "type": "CLIP", "links": [3], "slot_index": 0}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [7, 8, 21], "slot_index": 0}],
                "widgets_values": [NEGATIVE_PROMPT]
            },
            {
                "id": 4,
                "type": "EmptyLatentImage",
                "pos": [0, 150],
                "size": [320, 80],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [9], "slot_index": 0}],
                "widgets_values": [1, 1024, 1024]
            },
            {
                "id": 5,
                "type": "KSampler",
                "pos": [0, 550],
                "size": [320, 200],
                "inputs": [
                    {"name": "model", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "positive", "type": "CONDITIONING", "links": [5], "slot_index": 1},
                    {"name": "negative", "type": "CONDITIONING", "links": [7], "slot_index": 2},
                    {"name": "latent_image", "type": "LATENT", "links": [9], "slot_index": 3}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [10, 11], "slot_index": 0}],
                "widgets_values": [42, "fixed", 40, 6, "dpmpp_2m", "karras", 1.0]
            },
            {
                "id": 6,
                "type": "VAEDecode",
                "pos": [350, 550],
                "size": [220, 50],
                "inputs": [
                    {"name": "samples", "type": "LATENT", "links": [10], "slot_index": 0},
                    {"name": "vae", "type": "VAE", "links": [4], "slot_index": 1}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [12, 23], "slot_index": 0}]
            },
            {
                "id": 7,
                "type": "SaveImage",
                "pos": [600, 550],
                "size": [220, 50],
                "inputs": [{"name": "images", "type": "IMAGE", "links": [12], "slot_index": 0}],
                "widgets_values": [output_filename.replace('.png', '_base')]
            },
            {
                "id": 8,
                "type": "VAEEncode",
                "pos": [350, 350],
                "size": [220, 50],
                "inputs": [
                    {"name": "pixels", "type": "IMAGE", "links": [23], "slot_index": 0},
                    {"name": "vae", "type": "VAE", "links": [4], "slot_index": 1}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [13], "slot_index": 0}]
            },
            {
                "id": 9,
                "type": "KSampler",
                "pos": [900, 550],
                "size": [320, 200],
                "inputs": [
                    {"name": "model", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "positive", "type": "CONDITIONING", "links": [6], "slot_index": 1},
                    {"name": "negative", "type": "CONDITIONING", "links": [8], "slot_index": 2},
                    {"name": "latent_image", "type": "LATENT", "links": [13], "slot_index": 3}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [16], "slot_index": 0}],
                "widgets_values": [42, "fixed", 25, 5, "dpmpp_2m", "karras", 0.35]
            },
            {
                "id": 10,
                "type": "VAEDecode",
                "pos": [1250, 550],
                "size": [220, 50],
                "inputs": [
                    {"name": "samples", "type": "LATENT", "links": [16], "slot_index": 0},
                    {"name": "vae", "type": "VAE", "links": [4], "slot_index": 1}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [17, 18], "slot_index": 0}]
            },
            {
                "id": 11,
                "type": "SaveImage",
                "pos": [1500, 550],
                "size": [220, 50],
                "inputs": [{"name": "images", "type": "IMAGE", "links": [17], "slot_index": 0}],
                "widgets_values": [output_filename.replace('.png', '_refined')]
            },
            {
                "id": 12,
                "type": "LoadUpscaleModel",
                "pos": [1250, 100],
                "size": [260, 60],
                "outputs": [{"name": "upscale_model", "type": "UPSCALE_MODEL", "links": [19], "slot_index": 0}],
                "widgets_values": ["4x-UltraSharp.pth"]
            },
            {
                "id": 13,
                "type": "UltimateSDUpscale",
                "pos": [1500, 250],
                "size": [300, 400],
                "inputs": [
                    {"name": "image", "type": "IMAGE", "links": [18], "slot_index": 0},
                    {"name": "upscale_model", "type": "UPSCALE_MODEL", "links": [19], "slot_index": 1},
                    {"name": "positive", "type": "CONDITIONING", "links": [20], "slot_index": 2},
                    {"name": "negative", "type": "CONDITIONING", "links": [21], "slot_index": 3}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [22], "slot_index": 0}],
                "widgets_values": [1.5, "Linear", 8, "Half tile offset", 8, 32, "euler_ancestral", "normal", 25, 7, 0.35]
            },
            {
                "id": 14,
                "type": "SaveImage",
                "pos": [1850, 400],
                "size": [220, 50],
                "inputs": [{"name": "images", "type": "IMAGE", "links": [22], "slot_index": 0}],
                "widgets_values": [output_filename]
            }
        ],
        "links": [
            [1, 1, 0, 5, 0, "MODEL"],
            [2, 1, 1, 2, 0, "CLIP"],
            [3, 1, 1, 3, 0, "CLIP"],
            [4, 1, 2, 6, 1, "VAE"],
            [5, 2, 0, 5, 1, "CONDITIONING"],
            [6, 2, 0, 9, 1, "CONDITIONING"],
            [7, 3, 0, 5, 2, "CONDITIONING"],
            [8, 3, 0, 9, 2, "CONDITIONING"],
            [9, 4, 0, 5, 3, "LATENT"],
            [10, 5, 0, 6, 0, "LATENT"],
            [11, 5, 0, 8, 0, "LATENT"],
            [12, 6, 0, 7, 0, "IMAGE"],
            [23, 6, 0, 8, 0, "IMAGE"],
            [13, 8, 0, 9, 3, "LATENT"],
            [16, 9, 0, 10, 0, "LATENT"],
            [17, 10, 0, 11, 0, "IMAGE"],
            [18, 10, 0, 13, 0, "IMAGE"],
            [19, 12, 0, 13, 1, "UPSCALE_MODEL"],
            [20, 2, 0, 13, 2, "CONDITIONING"],
            [21, 3, 0, 13, 3, "CONDITIONING"],
            [22, 13, 0, 14, 0, "IMAGE"]
        ],
        "version": 0.4
    }
    
    return workflow

def generate_all_workflows():
    """Generate workflow JSON files for all prompts"""
    os.makedirs(WORKFLOW_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    prompts = parse_prompts_file(PROMPTS_FILE)
    
    print(f"Found {len(prompts)} prompts")
    
    workflow_files = []
    
    for i, prompt_data in enumerate(prompts):
        workflow = generate_workflow_json(
            prompt_data['prompt'], 
            prompt_data['filename']
        )
        
        workflow_path = os.path.join(WORKFLOW_DIR, f"cristie_{i:03d}_{prompt_data['lane']}.json")
        with open(workflow_path, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        workflow_files.append({
            'path': workflow_path,
            'title': prompt_data['title'],
            'lane': prompt_data['lane'],
            'category': prompt_data['category'],
            'filename': prompt_data['filename']
        })
        
        print(f"Generated: {prompt_data['title']} -> {workflow_path}")
    
    return workflow_files

def generate_batch_script(workflow_files):
    """Generate a bash script to run all workflows"""
    
    script_content = '''#!/bin/bash
# Cristie Desouza - Automated Batch Generation Script
# Run this script to generate all images automatically

set -e

echo "========================================"
echo "Cristie Desouza - Batch Image Generation"
echo "========================================"
echo ""

WORKFLOW_DIR="/workspace/runpod-slim/ComfyUI/user/default/workflows"
OUTPUT_DIR="/workspace/runpod-slim/ComfyUI/output/cristie_desouza"

mkdir -p "$OUTPUT_DIR"

# Function to queue a workflow and wait for completion
queue_workflow() {
    local workflow_file=$1
    local prompt_name=$2
    echo "Generating: $prompt_name"
    
    # Load and queue the workflow via ComfyUI API
    curl -X POST "http://127.0.0.1:8188/api/prompt" \\
        -H "Content-Type: application/json" \\
        -d "{\\"prompt\\": $(cat $workflow_file)}" \\
        > /dev/null 2>&1
    
    # Wait for completion (check output directory)
    local max_wait=300  # 5 minutes max per image
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if ls "$OUTPUT_DIR"/*.png 2>/dev/null | grep -q .; then
            echo "  ✓ Complete: $prompt_name"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done
    
    echo "  ✗ Timeout: $prompt_name"
    return 1
}

echo "Ready to generate $(echo "$WORKFLOW_FILES" | wc -l) images"
echo ""
echo "Starting generation..."
echo ""

# Generate each workflow
WORKFLOW_FILES_PLACEHOLDER

echo ""
echo "========================================"
echo "Batch generation complete!"
echo "Output directory: $OUTPUT_DIR"
echo "========================================"
'''
    
    # Replace placeholder with actual file list
    file_list = ""
    for wf in workflow_files:
        file_list += f'queue_workflow "{wf["path"]}" "{wf["title"]}"\n'
    
    script_content = script_content.replace("WORKFLOW_FILES_PLACEHOLDER", file_list.strip())
    
    script_path = "/workspace/runpod-slim/ComfyUI/generate_cristie_batch.sh"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"\nGenerated batch script: {script_path}")

def main():
    print("=" * 60)
    print("Cristie Desouza - Automated Prompt & Workflow Generator")
    print("=" * 60)
    print()
    
    # Parse prompts
    print("Parsing prompts file...")
    prompts = parse_prompts_file(PROMPTS_FILE)
    print(f"Found {len(prompts)} prompts")
    print()
    
    # Count by lane
    lanes = {}
    for p in prompts:
        lanes[p['lane']] = lanes.get(p['lane'], 0) + 1
    
    for lane, count in sorted(lanes.items()):
        print(f"  {lane}: {count} prompts")
    print()
    
    # Generate workflows
    print("Generating ComfyUI workflows...")
    workflow_files = generate_all_workflows()
    print()
    
    # Generate batch script
    print("Generating batch script...")
    generate_batch_script(workflow_files)
    print()
    
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print()
    print("To run all generations automatically:")
    print(f"  cd /workspace/runpod-slim/ComfyUI")
    print("  ./generate_cristie_batch.sh")
    print()
    print("Or run individual workflows from:")
    print(f"  {WORKFLOW_DIR}/")
    print()
    print("Outputs will be saved to:")
    print(f"  {OUTPUT_DIR}/")
    print()

if __name__ == "__main__":
    main()
