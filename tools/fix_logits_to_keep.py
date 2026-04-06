#!/usr/bin/env python3
"""
Fix num_logits_to_keep parameter in modeling_dots_ocr.py
This parameter was added in later transformers versions but not in 4.45.0
"""
import sys

def fix_logits_to_keep(file_path):
    """Remove num_logits_to_keep parameter to avoid compatibility issues"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Remove num_logits_to_keep from the method signature
        old_signature = '''    def prepare_inputs_for_generation(
        self,
        input_ids,
        past_key_values=None,
        inputs_embeds=None,
        pixel_values=None,
        image_grid_thw=None,
        attention_mask=None,
        cache_position=None,
        num_logits_to_keep=None,
        **kwargs,
    ):'''

        new_signature = '''    def prepare_inputs_for_generation(
        self,
        input_ids,
        past_key_values=None,
        inputs_embeds=None,
        pixel_values=None,
        image_grid_thw=None,
        attention_mask=None,
        cache_position=None,
        **kwargs,
    ):'''

        if old_signature in content:
            content = content.replace(old_signature, new_signature)
            print("✓ Removed num_logits_to_keep from method signature")
        else:
            print("✓ Method signature already updated or pattern not found")

        # Remove num_logits_to_keep from the super() call
        old_super_call = '''        model_inputs = super().prepare_inputs_for_generation(
            input_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            cache_position=cache_position,
            num_logits_to_keep=num_logits_to_keep,
            **kwargs,
        )'''

        new_super_call = '''        model_inputs = super().prepare_inputs_for_generation(
            input_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            cache_position=cache_position,
            **kwargs,
        )'''

        if old_super_call in content:
            content = content.replace(old_super_call, new_super_call)
            print("✓ Removed num_logits_to_keep from super() call")
        else:
            print("✓ Super call already updated or pattern not found")

        # Write the fixed content
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"✓ Successfully fixed {file_path}")
        return True

    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os

    model_file = "/model/modeling_dots_ocr.py"

    # Allow passing different path as argument
    if len(sys.argv) > 1:
        model_file = sys.argv[1]

    if os.path.exists(model_file):
        success = fix_logits_to_keep(model_file)
        sys.exit(0 if success else 1)
    else:
        print(f"⚠ Model file not found: {model_file}")
        sys.exit(1)
