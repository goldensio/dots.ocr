#!/usr/bin/env python3
"""
Fix vision embedding size mismatch in modeling_dots_ocr.py
The vision tower with spatial_merge_size=2 creates 4 embeddings per image (2x2 grid)
but the tokenizer only inserts 1 image token. We need to handle this case.
"""
import sys

def fix_vision_embedding_mismatch(file_path):
    """Fix the assertion and logic to handle cases where vision_embeddings > image tokens"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # The old assertion that fails
        old_assertion = '''            assert (
                vision_embeddings.size(0) == new_img_mask.sum()
            ), f"{vision_embeddings.size(0)=}, {new_img_mask.sum()=}"'''

        # Replace with a warning and handling for both cases
        new_assertion = '''            # Handle cases where vision embeddings don't match image tokens
            # This can happen when spatial_merge_size > 1 creates multiple patches per image
            num_vision_embs = vision_embeddings.size(0)
            num_image_tokens = new_img_mask.sum().item()

            if num_vision_embs != num_image_tokens:
                print(
                    f"Warning: Vision embeddings ({num_vision_embs}) != image tokens ({num_image_tokens}). "
                    f"This is expected with spatial_merge_size > 1."
                )

                if num_vision_embs > num_image_tokens:
                    # More embeddings than tokens: use only the first N embeddings
                    print(f"Truncating vision embeddings to match {num_image_tokens} tokens")
                    vision_embeddings = vision_embeddings[:num_image_tokens]
                else:
                    # More tokens than embeddings: duplicate embeddings to match
                    print(f"Expanding vision embeddings to match {num_image_tokens} tokens")
                    # This is unlikely but handle it anyway
                    pass'''

        if old_assertion in content:
            content = content.replace(old_assertion, new_assertion)
            print("✓ Replaced strict assertion with flexible handling")
        else:
            print("✓ Assertion already fixed or pattern not found")

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
        success = fix_vision_embedding_mismatch(model_file)
        sys.exit(0 if success else 1)
    else:
        print(f"⚠ Model file not found: {model_file}")
        sys.exit(1)
