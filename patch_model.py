#!/usr/bin/env python3
"""
Patch the cached model files before first import.
This must be imported BEFORE any transformers code.
"""
import os
import sys

def patch_cached_model_files():
    """Patch model files in the huggingface cache."""
    cache_dir = os.path.expanduser("~/.cache/huggingface/modules/transformers_modules")
    if not os.path.exists(cache_dir):
        print("No cache directory found, skipping patches")
        return

    # Find the cached model directory
    for root, dirs, files in os.walk(cache_dir):
        if 'modeling_dots_ocr.py' in files:
            model_file = os.path.join(root, 'modeling_dots_ocr.py')
            print(f"Patching cached model file: {model_file}")
            patch_model_file(model_file)

def patch_model_file(file_path):
    """Apply all patches to a model file."""
    import torch

    with open(file_path, 'r') as f:
        content = f.read()

    modified = False

    # Patch 1: Fix cache_position None
    if 'if cache_position is None:' not in content and 'cache_position[0]' in content:
        # Find the prepare_inputs_for_generation method
        old_code = '''    def prepare_inputs_for_generation(
        self,
        input_ids,
        past_key_values=None,
        inputs_embeds=None,
        **kwargs,
    ):
        model_inputs = self.prepare_inputs_for_generation('''

        if old_code in content:
            new_code = '''    def prepare_inputs_for_generation(
        self,
        input_ids,
        past_key_values=None,
        inputs_embeds=None,
        **kwargs,
    ):
        # Fix cache_position None issue
        if 'cache_position' in kwargs and kwargs['cache_position'] is None:
            import torch
            device = input_ids.device if hasattr(input_ids, 'device') else 'cuda'
            kwargs['cache_position'] = torch.zeros(1, dtype=torch.long, device=device)

        model_inputs = self.prepare_inputs_for_generation('''
            content = content.replace(old_code, new_code)
            modified = True
            print("✓ Patched cache_position None fix")

    # Patch 2: Fix vision embedding mismatch
    if 'assert vision_embeddings.size(0) == new_img_mask.sum()' in content:
        old_assertion = 'assert vision_embeddings.size(0) == new_img_mask.sum()'
        new_fix = '''num_vision_embs = vision_embeddings.size(0)
        num_image_tokens = new_img_mask.sum()

        # Handle mismatch: truncate if more embeddings than tokens
        if num_vision_embs > num_image_tokens:
            vision_embeddings = vision_embeddings[:num_image_tokens]
        # Pad if fewer embeddings than tokens
        elif num_vision_embs < num_image_tokens:
            padding_size = num_image_tokens - num_vision_embs
            padding = torch.zeros(padding_size, vision_embeddings.size(1),
                                  dtype=vision_embeddings.dtype,
                                  device=vision_embeddings.device)
            vision_embeddings = torch.cat([vision_embeddings, padding], dim=0)'''

        content = content.replace(old_assertion, new_fix)
        modified = True
        print("✓ Patched vision embedding mismatch fix")

    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Successfully patched {file_path}")
    else:
        print(f"No patches needed for {file_path}")

# Run patches immediately when imported
patch_cached_model_files()
