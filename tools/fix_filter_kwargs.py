#!/usr/bin/env python3
"""
Fix logits_to_keep error by filtering it from **kwargs in forward()
This intercepts kwargs and removes unsupported parameters for transformers 4.45.0
"""
import sys

def fix_filter_kwargs(file_path):
    """Filter logits_to_keep and num_logits_to_keep from **kwargs in forward()"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Find the forward method and add kwargs filtering
        old_forward_start = '''    def forward(
        self,
        input_ids: torch.LongTensor,
        pixel_values: Optional[torch.FloatTensor] = None,
        image_grid_thw: Optional[torch.FloatTensor] = None,
        inputs_embeds: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[torch.FloatTensor]] = None,
        labels: Optional[torch.LongTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ) -> Union[Tuple, CausalLMOutputWithPast]:'''

        new_forward_start = '''    def forward(
        self,
        input_ids: torch.LongTensor,
        pixel_values: Optional[torch.FloatTensor] = None,
        image_grid_thw: Optional[torch.FloatTensor] = None,
        inputs_embeds: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[torch.FloatTensor]] = None,
        labels: Optional[torch.LongTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        **kwargs,  # Accept **kwargs to filter out unsupported parameters
    ) -> Union[Tuple, CausalLMOutputWithPast]:
        # Filter out unsupported parameters for transformers 4.45.0 compatibility
        # Remove logits_to_keep and num_logits_to_keep from kwargs
        kwargs.pop('logits_to_keep', None)
        kwargs.pop('num_logits_to_keep', None)'''

        if old_forward_start in content:
            content = content.replace(old_forward_start, new_forward_start)
            print("✓ Added **kwargs parameter and filtering to forward() method")
        else:
            print("✓ Forward method already has **kwargs or pattern not found")

        # Now modify the super().forward() call to pass filtered kwargs
        old_super_forward = '''        outputs = super().forward(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
        )'''

        new_super_forward = '''        outputs = super().forward(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            **kwargs,  # Pass filtered kwargs
        )'''

        if old_super_forward in content:
            content = content.replace(old_super_forward, new_super_forward)
            print("✓ Modified super().forward() to pass filtered kwargs")
        else:
            print("✓ Super forward call already modified or pattern not found")

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
