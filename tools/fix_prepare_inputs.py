#!/usr/bin/env python3
"""
Fix prepare_inputs_for_generation to include image_grid_thw in model_inputs
The method was only passing pixel_values but not image_grid_thw
"""
import sys

def fix_prepare_inputs(file_path):
    """Add image_grid_thw to model_inputs in prepare_inputs_for_generation"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # First, we need to add image_grid_thw as a parameter to prepare_inputs_for_generation
        old_method_def = '''    def prepare_inputs_for_generation(
        self,
        input_ids,
        past_key_values=None,
        inputs_embeds=None,
        pixel_values=None,
        attention_mask=None,
        cache_position=None,
        num_logits_to_keep=None,
        **kwargs,
    ):'''

        new_method_def = '''    def prepare_inputs_for_generation(
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

        if old_method_def in content:
            content = content.replace(old_method_def, new_method_def)
            print("✓ Added image_grid_thw parameter to prepare_inputs_for_generation")
        else:
            print("✓ Method definition already updated or not found")

        # Now fix the model_inputs assignment
        old_assignment = '''        if cache_position[0] == 0:
            model_inputs["pixel_values"] = pixel_values

        return model_inputs'''

        new_assignment = '''        if cache_position[0] == 0:
            model_inputs["pixel_values"] = pixel_values
            model_inputs["image_grid_thw"] = image_grid_thw

        return model_inputs'''

        if old_assignment in content:
            content = content.replace(old_assignment, new_assignment)
            print("✓ Added image_grid_thw to model_inputs")
        else:
            print("✓ Model inputs assignment already updated or pattern not found")

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
        success = fix_prepare_inputs(model_file)
        sys.exit(0 if success else 1)
    else:
        print(f"⚠ Model file not found: {model_file}")
        sys.exit(1)
