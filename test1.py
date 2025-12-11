import os
import torch
import warnings
from bisect import bisect_left
warnings.filterwarnings("ignore")

from modelscope import AutoProcessor
from modeling_bailingmm2 import BailingMM2NativeForConditionalGeneration

def split_model():
    device_map = {}
    world_size = torch.cuda.device_count()
    num_layers = 32
    layer_per_gpu = num_layers // world_size
    layer_per_gpu = [i * layer_per_gpu for i in range(1, world_size + 1)]
    for i in range(num_layers):
        device_map[f'model.model.layers.{i}'] = bisect_left(layer_per_gpu, i)
    device_map['vision'] = 0
    device_map['audio'] = 0
    device_map['linear_proj'] = 0
    device_map['linear_proj_audio'] = 0
    device_map['model.model.word_embeddings.weight'] = 0
    device_map['model.model.norm.weight'] = 0
    device_map['model.lm_head.weight'] = 0
    device_map['model.model.norm'] = 0
    device_map[f'model.model.layers.{num_layers - 1}'] = 0
    return device_map

# Load pre-trained model with optimized settings, this will take ~10 minutes
model_path = "inclusionAI/Ming-flash-omni-Preview"
model = BailingMM2NativeForConditionalGeneration.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",
    device_map=split_model(),
    load_image_gen=True,
    load_talker=True,
).to(dtype=torch.bfloat16)

# Initialize processor for handling multimodal inputs
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

# Inference Pipeline
def generate(messages, processor, model, sys_prompt_exp=None, use_cot_system_prompt=False, max_new_tokens=512):
    text = processor.apply_chat_template(
        messages,
        sys_prompt_exp=sys_prompt_exp,
        use_cot_system_prompt=use_cot_system_prompt
    )
    image_inputs, video_inputs, audio_inputs = processor.process_vision_info(messages)

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        audios=audio_inputs,
        return_tensors="pt",
        audio_kwargs={"use_whisper_encoder": True},
    ).to(model.device)

    for k in inputs.keys():
        if k == "pixel_values" or k == "pixel_values_videos" or k == "audio_feats":
            inputs[k] = inputs[k].to(dtype=torch.bfloat16)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            eos_token_id=processor.gen_terminator,
            num_logits_to_keep=1,
        )

    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]

    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    return output_text

# qa
messages = [
    {
        "role": "HUMAN",
        "content": [
            {"type": "text", "text": "请详细介绍鹦鹉的生活习性。"}
        ],
    },
]
output_text = generate(messages, processor=processor, model=model)
print(output_text)
# Output:

# 鹦鹉是一种非常聪明和社交性强的鸟类，它们的生活习性非常丰富和有趣。以下是一些关于鹦鹉生活习性的详细介绍：
# ### 1. **栖息地**
# 鹦鹉主要分布在热带和亚热带地区，包括非洲、亚洲、澳大利亚和南美洲。它们通常生活在森林、草原、沙漠和城市环境中。不同种类的鹦鹉对栖息地的要求有所不同，但大多数鹦鹉喜欢有丰富植被和水源的地方。
# ### 2. **饮食**
# 鹦鹉是杂食性动物，它们的饮食非常多样化。它们的食物包括种子、坚果、水果、蔬菜、花蜜和昆虫。鹦鹉的喙非常强壮，能够轻松地打开坚硬的果壳和坚果。一些鹦鹉还会吃泥土或沙子，以帮助消化和补充矿物质。
# ......