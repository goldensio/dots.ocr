#!/usr/bin/env python3
"""
Fix logits_to_keep error by removing it completely from forward()
The transformers 4.45.0 Qwen2ForCausalLM.forward() doesn't support logits_to_keep
"""
import sys

def fix_filter_kwargs(file_path):
    """Remove logits_to_keep from forward() signature and super() call"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Fix 1: Remove logits_to_keep from the method signature
        old_signature = '''        logits_to_keep: int = 0,
        **loss_kwargs,'''

        new_signature = '''        **loss_kwargs,'''

        if old_signature in content:
            content = content.replace(old_signature, new_signature)
            print("✓ Removed logits_to_keep from forward() signature")
        else:
            print("✓ Forward signature already updated or pattern not found")

        # Fix 2: Filter logits_to_keep from loss_kwargs before processing
        old_return = '''    ) -> Union[Tuple, CausalLMOutputWithPast]:
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict'''

        new_return = '''    ) -> Union[Tuple, CausalLMOutputWithPast]:
        # Filter out logits_to_keep from loss_kwargs for transformers 4.45.0 compatibility
        loss_kwargs.pop('logits_to_keep', None)
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict'''

        if old_return in content:
            content = content.replace(old_return, new_return)
            print("✓ Added logits_to_keep filtering from loss_kwargs")
        else:
            print("✓ Filtering already added or pattern not found")

        # Fix 3: Remove logits_to_keep from the super().forward() call
        old_super_call = '''            # return_dict=return_dict,
            logits_to_keep=logits_to_keep,
            **loss_kwargs,
        )'''

        new_super_call = '''            # return_dict=return_dict,
            **loss_kwargs,
        )'''

        if old_super_call in content:
            content = content.replace(old_super_call, new_super_call)
            print("✓ Removed logits_to_keep from super().forward() call")
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
        success = fix_filter_kwargs(model_file)
        sys.exit(0 if success else 1)
    else:
        print(f"⚠ Model file not found: {model_file}")
        sys.exit(1)
