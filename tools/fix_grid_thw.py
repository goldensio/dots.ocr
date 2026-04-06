#!/usr/bin/env python3
"""
Fix grid_thw None error in modeling_dots_ocr.py
The code checks if pixel_values is not None but doesn't check if grid_thw is not None
before accessing grid_thw.shape[0]
"""
import sys

def fix_grid_thw_none(file_path):
    """Add None check for grid_thw before accessing .shape"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # The problematic code that checks grid_thw.shape without checking if grid_thw is None
        old_code = '''        if pixel_values is not None:
            assert img_mask is not None
            if grid_thw.shape[0] > DOTS_VLM_MAX_IMAGES:'''

        # Fixed version that checks grid_thw is not None first
        new_code = '''        if pixel_values is not None:
            assert img_mask is not None
            assert grid_thw is not None, "grid_thw cannot be None when pixel_values is not None"
            if grid_thw.shape[0] > DOTS_VLM_MAX_IMAGES:'''

        if old_code in content:
            content = content.replace(old_code, new_code)
            print("✓ Added None check for grid_thw before accessing .shape")
        else:
            print("✓ Grid_thw fix already applied or code pattern not found")
            # Check if it's already fixed
            if "assert grid_thw is not None" in content:
                print("✓ Grid_thw None check already exists")

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
        success = fix_grid_thw_none(model_file)
        sys.exit(0 if success else 1)
    else:
        print(f"⚠ Model file not found: {model_file}")
        sys.exit(1)
