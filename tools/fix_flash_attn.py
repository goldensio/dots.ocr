#!/usr/bin/env python3
"""
Fix flash_attn import and model config after downloading model weights.
This script is run after downloading model weights to make flash_attn truly optional
and fix dtype compatibility issues.
"""
import re
import sys
import json

def fix_flash_attn_import(file_path):
    """Make flash_attn import optional in the model file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Fix 1: Make the import optional
        old_import_pattern = r'from flash_attn import flash_attn_varlen_func'
        new_import = '''try:
    from flash_attn import flash_attn_varlen_func
    HAS_FLASH_ATTN = True
except ImportError:
    HAS_FLASH_ATTN = False
    flash_attn_varlen_func = None'''

        if re.search(old_import_pattern, content):
            content = re.sub(old_import_pattern, new_import, content)
            print("✓ Made flash_attn import optional")
        else:
            print("✓ Flash_attn import already fixed or not found")

        # Fix 2: Update the attention class mapping to use fallback
        old_mapping = '''"flash_attention_2": VisionFlashAttention2,'''
        new_mapping = '''"flash_attention_2": VisionFlashAttention2 if HAS_FLASH_ATTN else VisionSdpaAttention,'''

        if old_mapping in content:
            content = content.replace(old_mapping, new_mapping)
            print("✓ Added fallback for flash_attention_2")

        # Write the fixed content
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"✓ Successfully fixed {file_path}")
        return True

    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}", file=sys.stderr)
        return False

def fix_model_config(config_path):
    """Fix torch_dtype in model config.json - remove it to allow auto-detection."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        original_dtype = config.get("torch_dtype")
        print(f"Original torch_dtype in config: {original_dtype}")

        # Remove torch_dtype from config to allow auto-detection from checkpoint
        # This prevents dtype mismatch errors
        if "torch_dtype" in config:
            del config["torch_dtype"]
            print("✓ Removed torch_dtype from config (will use auto-detection)")
        else:
            print("✓ torch_dtype not in config, no change needed")

        # Write the fixed config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✓ Successfully fixed {config_path}")
        return True

    except Exception as e:
        print(f"✗ Error fixing {config_path}: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    import os

    model_file = "/model/modeling_dots_vision.py"
    config_file = "/model/config.json"

    # Allow passing different paths as arguments
    if len(sys.argv) > 1:
        model_file = sys.argv[1]
    if len(sys.argv) > 2:
        config_file = sys.argv[2]

    success = True

    # Fix modeling file
    if os.path.exists(model_file):
        success &= fix_flash_attn_import(model_file)
    else:
        print(f"⚠ Model file not found: {model_file}")

    # Fix config file
    if os.path.exists(config_file):
        success &= fix_model_config(config_file)
    else:
        print(f"⚠ Config file not found: {config_file}")

    sys.exit(0 if success else 1)
