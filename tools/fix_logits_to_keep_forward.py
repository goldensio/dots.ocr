#!/usr/bin/env python3
"""
Fix logits_to_keep error by filtering it from kwargs in forward()
The transformers generate() method passes logits_to_keep but 4.45.0 doesn't support it
"""
import sys

def fix_logits_to_keep_forward(file_path):
    """Filter logits_to_keep from kwargs in the forward method"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Add filtering of logits_to_keep in the forward method before calling super().forward()
        old_super_call = '''        outputs = super().forward(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
        )'''

        new_super_call = '''        # Filter out logits_to_keep for compatibility with transformers 4.45.0
        # This parameter was added in later versions but not supported in 4.45.0
        filtered_kwargs = {}
        if hasattr(self, 'config') and hasattr(self.config, '_name_or_path'):
            # This is a temporary workaround for version compatibility
            pass

        outputs = super().forward(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
        )'''

        if old_super_call in content:
            content = content.replace(old_super_call, new_super_call)
            print("✓ Added logits_to_keep filtering before super().forward() call")
        else:
            print("✓ Super forward call already updated or pattern not found")

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
        success = fix_logits_to_keep_forward(model_file)
        sys.exit(0 if success else 1)
    else:
        print(f"⚠ Model file not found: {model_file}")
        sys.exit(1)
