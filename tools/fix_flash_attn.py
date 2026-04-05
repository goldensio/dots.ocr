#!/usr/bin/env python3
"""
Fix flash_attn import in modeling_dots_vision.py to make it optional.
This script is run after downloading model weights to make flash_attn truly optional.
"""
import re
import sys

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

if __name__ == "__main__":
    import os

    # Default path
    model_file = "/model/modeling_dots_vision.py"

    # Allow passing a different path as argument
    if len(sys.argv) > 1:
        model_file = sys.argv[1]

    if not os.path.exists(model_file):
        print(f"✗ File not found: {model_file}", file=sys.stderr)
        sys.exit(1)

    success = fix_flash_attn_import(model_file)
    sys.exit(0 if success else 1)
