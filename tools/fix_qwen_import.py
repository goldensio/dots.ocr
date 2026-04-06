#!/usr/bin/env python3
"""
Fix Qwen2_5_VLProcessor import to be optional for compatibility with transformers 4.45.0
and PyTorch 2.1.2 (needed for CUDA 11.8).
"""
import re
import sys

def fix_qwen_import(file_path):
    """Make Qwen2_5_VLProcessor import optional and provide fallback."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Fix 1: Make the import optional
        old_import = '''from transformers import Qwen2_5_VLProcessor, AutoProcessor'''

        new_import = '''try:
    from transformers import Qwen2_5_VLProcessor
    HAS_QWEN2_5_VL = True
except ImportError:
    # Qwen2_5_VLProcessor not available (transformers < 4.46.0)
    # Fall back to Qwen2VLProcessor which is available in 4.45.0
    try:
        from transformers import Qwen2VLProcessor as Qwen2_5_VLProcessor
        HAS_QWEN2_5_VL = True
    except ImportError:
        HAS_QWEN2_5_VL = False
        Qwen2_5_VLProcessor = None

from transformers import AutoProcessor'''

        if old_import in content:
            content = content.replace(old_import, new_import)
            print("✓ Made Qwen2_5_VLProcessor import optional")
        else:
            print("✓ Import already fixed or not found")

        # Fix 2: Update DotsVLProcessor to use fallback
        old_class = '''class DotsVLProcessor(Qwen2_5_VLProcessor):'''

        new_class = '''class DotsVLProcessor(Qwen2_5_VLProcessor if HAS_QWEN2_5_VL else AutoProcessor):
    """Dots Vision-Language Processor for OCR tasks."""

    def __init__(self, image_processor=None, tokenizer=None, video_processor=None, chat_template=None, **kwargs):
        # Remove chat_template from kwargs to avoid duplicate argument error
        kwargs.pop('chat_template', None)

        if HAS_QWEN2_5_VL:
            # Use Qwen2_5_VLProcessor or Qwen2VLProcessor
            super().__init__(image_processor, tokenizer, video_processor, chat_template=chat_template, **kwargs)
        else:
            # Fallback to AutoProcessor
            AutoProcessor.__init__(self, image_processor, tokenizer, video_processor, chat_template=chat_template, **kwargs)

        self.image_token = "<|imgpad|>" if not hasattr(tokenizer, "image_token") else tokenizer.image_token
        self.image_token_id = 151665
        self.video_token = "<|video_pad|>" if not hasattr(tokenizer, "video_token") else tokenizer.video_token
        self.video_token_id = 151656

    # Add any missing methods from parent if needed
    if not HAS_QWEN2_5_VL:
        def __call__(self, *args, **kwargs):
            """Forward to AutoProcessor's call method."""
            return AutoProcessor.__call__(self, *args, **kwargs)'''

        if old_class in content:
            content = content.replace(old_class, new_class)
            print("✓ Added fallback for DotsVLProcessor")
        else:
            print("✓ DotsVLProcessor already patched or not found")

        # Also fix the original __init__ if it exists separately
        old_init = '''    def __init__(self, image_processor=None, tokenizer=None, video_processor=None, chat_template=None, **kwargs):
        super().__init__(image_processor, tokenizer, video_processor, chat_template=chat_template)
        self.image_token = "<|imgpad|>" if not hasattr(tokenizer, "image_token") else tokenizer.image_token
        self.image_token_id = 151665
        self.video_token = "<|video_pad|>" if not hasattr(tokenizer, "video_token") else tokenizer.video_token
        self.video_token_id = 151656'''

        if old_init in content:
            content = content.replace(old_init, '')
            print("✓ Removed duplicate __init__ method")

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

    config_file = "/model/configuration_dots.py"

    # Allow passing different path as argument
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    if os.path.exists(config_file):
        success = fix_qwen_import(config_file)
        sys.exit(0 if success else 1)
    else:
        print(f"⚠ Config file not found: {config_file}")
        sys.exit(1)
