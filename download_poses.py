#!/usr/bin/env python3
"""
Pose Reference Downloader for AI Model Content Creation
Downloads and organizes pose reference images from free sources.
"""

import os
import urllib.request
import urllib.error
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent / "models"
MODELS = {
    "cristie_desouza": {
        "search_terms": [
            "bikini model pose",
            "beach fashion pose",
            "confident woman standing",
            "DJ booth photo",
            "sexy swimwear pose",
            "confident female pose",
            "beach photoshoot"
        ],
        "categories": ["standing", "seated", "reclining", "action"]
    },
    "lexi_fairfax": {
        "search_terms": [
            "equestrian woman pose",
            "rock climbing female",
            "british fashion pose",
            "elegant woman standing",
            "outdoor adventure pose",
            "horse riding pose",
            "country estate fashion"
        ],
        "categories": ["standing", "seated", "action", "equestrian"]
    },
    "mia_delacroix": {
        "search_terms": [
            "business woman pose",
            "hotel suite photo",
            "elegant woman seated",
            "silk robe pose",
            "luxury travel photo",
            "flight attendant uniform",
            "sultry elegant pose"
        ],
        "categories": ["standing", "seated", "reclining", "uniform"]
    }
}

# Free image sources (direct URLs - no API key needed)
IMAGE_SOURCES = {
    "unsplash": {
        "base_url": "https://images.unsplash.com",
        "search_url": "https://unsplash.com/napi/search?query={query}&per_page=30"
    },
    "pexels": {
        "base_url": "https://images.pexels.com/photos",
        "api_url": "https://api.pexels.com/v1/search?query={query}&per_page=30"
    }
}

def create_folder_structure():
    """Create the required folder structure."""
    for model_name in MODELS.keys():
        model_dir = BASE_DIR / model_name / "poses" / "base"
        for category in MODELS[model_name]["categories"]:
            (model_dir / category).mkdir(parents=True, exist_ok=True)
    print("✅ Folder structure created")

def download_image(url, save_path, timeout=30):
    """Download a single image with error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            with open(save_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False

def download_from_pexels(api_key, query, output_dir, num_images=10):
    """Download images from Pexels using API."""
    if not api_key:
        print("⚠️  No Pexels API key provided. Skipping Pexels.")
        return []
    
    import json
    import ssl
    
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={num_images}"
    headers = {'Authorization': api_key}
    
    try:
        # Create SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
            data = json.loads(response.read().decode())
            photos = data.get('photos', [])
            
            downloaded = []
            for i, photo in enumerate(photos[:num_images]):
                src = photo.get('src', {})
                image_url = src.get('medium') or src.get('original')
                if image_url:
                    ext = os.path.splitext(image_url)[1] or '.jpg'
                    save_path = output_dir / f"{query.replace(' ', '_')}_{i}{ext}"
                    if download_image(image_url, save_path):
                        downloaded.append(str(save_path))
            return downloaded
    except Exception as e:
        print(f"❌ Pexels API error: {e}")
        return []

def download_from_placeholder_sources(output_dir, model_name, category):
    """
    Download from placeholder/free sources.
    NOTE: Most stock sites require API keys or have protections.
    This creates a manual download guide instead.
    """
    
    guide_file = output_dir.parent / "DOWNLOAD_GUIDE.txt"
    
    guide_content = f"""
# Pose Reference Download Guide for {model_name}

Since automated access to stock photo sites is limited, please manually download
images from these sources and save them to this folder.

## Categories Needed: {', '.join(MODELS[model_name]['categories'])}

## Search Terms for Each Category:

### Standing Poses:
- "confident woman standing pose"
- "fashion model standing pose"
- "sexy standing pose reference"

### Seated Poses:
- "elegant woman seated pose"
- "fashion seated pose reference"
- "sexy sitting pose"

### Reclining Poses:
- "bikini reclining pose"
- "lingerie reclining pose"
- "beach reclining pose"

### Action Poses (Model-Specific):
- For Cristie: "DJ posing", "beach dancing", "surfing pose"
- For Lexi: "horse riding pose", "rock climbing", "motorcycle pose"
- For Mia: "flight attendant pose", "hotel suite pose", "silk robe pose"

## Free Sources:
1. **Pinterest** - Search each term, right-click "Save image"
2. **Google Images** - Search → Tools → Usage rights → Creative Commons
3. **Unsplash** - https://unsplash.com (free, no account needed)
4. **Pexels** - https://pexels.com (free, may need API key)

## Quick Download Steps:
1. Open Pinterest or Google Images
2. Search: "[model] pose reference [category]"
3. Filter: "Usage rights" → "Creative Commons" or "Free to use"
4. Download 10-15 images per category
5. Save to: this folder
6. Rename: use category numbering (standing_01.jpg, standing_02.jpg, etc.)

## File Naming Convention:
- standing_01.jpg, standing_02.jpg, ...
- seated_01.jpg, seated_02.jpg, ...
- reclining_01.jpg, reclining_02.jpg, ...
"""
    
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    print(f"📄 Created download guide: {guide_file}")

def create_sample_poses_with_ai(output_dir, category):
    """
    Placeholder for AI pose generation.
    Once you have ComfyUI running with ControlNet, you can generate
    clean pose templates from any reference image.
    """
    
    readme_file = output_dir.parent / "AI_POSE_GENERATION.txt"
    
    readme_content = f"""
# AI Pose Generation (ControlNet OpenPose)

Once ComfyUI is running with ControlNet, you can generate clean pose templates
from any reference image.

## Workflow:
1. Load any reference image (Pinterest, stock photo, etc.)
2. Connect to OpenPose ControlNet node
3. Extract pose skeleton (clean, no face/body, just skeleton)
4. Save as pose template for InstantID generation

## Purpose:
- Extract pose from professional photoshoots
- Create reusable pose templates
- Build your custom library over time

## When Ready:
Use ComfyUI → ControlNet → OpenPose to extract poses from your reference images.
"""
    
    with open(readme_file, 'w') as f:
        f.write(readme_content)

def main():
    """Main execution function."""
    print("=" * 60)
    print("📸 AI Model Pose Reference Downloader")
    print("=" * 60)
    
    # Create folder structure
    create_folder_structure()
    
    # Check for Pexels API key
    pexels_api_key = os.environ.get("PEXELS_API_KEY", "")
    
    # For each model, create download guides
    for model_name, config in MODELS.items():
        print(f"\n📁 Processing: {model_name}")
        
        output_dir = BASE_DIR / model_name / "poses" / "base"
        
        # Create download guide
        download_from_placeholder_sources(output_dir, model_name, config["categories"])
        
        # Create AI generation guide
        create_sample_poses_with_ai(output_dir, model_name[""] if isinstance(model_name, dict) else model_name)
        
        # Try Pexels if API key available
        if pexels_api_key:
            for search_term in config["search_terms"][:2]:  # First 2 terms per model
                category_dir = output_dir / config["categories"][0]
                download_from_pexels(pexels_api_key, search_term, category_dir, num_images=5)
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Download reference images using the guides in each folder")
    print("2. OR set PEXELS_API_KEY env variable and re-run for auto-download")
    print("3. Once images are ready, use ComfyUI + ControlNet to extract poses")
    print("4. Run InstantID to swap faces onto your pose templates")

if __name__ == "__main__":
    main()
