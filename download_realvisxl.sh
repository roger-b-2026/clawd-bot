#!/bin/bash
# Download RealVisXL V5.0 to ComfyUI checkpoints folder

# Navigate to ComfyUI models folder (adjust path if different)
cd /workspace/ComfyUI/models/checkpoints

# Download RealVisXL V5.0 fp16 (recommended - smaller, almost same quality)
echo "Downloading RealVisXL_V5.0_fp16.safetensors..."
wget -L "https://huggingface.co/SG161222/RealVisXL_V5.0/resolve/main/RealVisXL_V5.0_fp16.safetensors" -O RealVisXL_V5.0_fp16.safetensors

# Verify download
if [ -f "RealVisXL_V5.0_fp16.safetensors" ]; then
    echo "✅ Download complete!"
    ls -lh RealVisXL_V5.0_fp16.safetensors
else
    echo "❌ Download failed"
fi

# Alternative: Download full fp32 version (larger, higher precision)
# wget -L "https://huggingface.co/SG161222/RealVisXL_V5.0/resolve/main/RealVisXL_V5.0_fp32.safetensors" -O RealVisXL_V5.0_fp32.safetensors
