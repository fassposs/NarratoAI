import os
import torch
from PIL import Image
from diffusers import QwenImageEditPlusPipeline


device = "cuda" if torch.cuda.is_available() else "cpu"
pipeline = QwenImageEditPlusPipeline.from_pretrained("Qwen/Qwen-Image-Edit-2509", torch_dtype=torch.bfloat16).to(device)
print("pipeline loaded")

# pipeline.to('cuda')
pipeline.set_progress_bar_config()
image1 = Image.open("./testInput/test001.png").convert("RGB") # Image.open("./testInput/test001.png")
prompt = "给出的图片是电影的截图,如果有字幕的话,请帮忙去掉图片的字幕."
inputs = {
    "image": [image1],
    "prompt": prompt,
    "generator": torch.manual_seed(0),
    "true_cfg_scale": 4.0,
    "negative_prompt": " ",
    "num_inference_steps": 40,
    "guidance_scale": 1.0,
    "num_images_per_prompt": 1
}
with torch.inference_mode():
    output = pipeline(**inputs)
    output_image = output.images[0]
    output_image.save("./testOutput/test001.png")
    print("image saved at", os.path.abspath("./testOutput/test001.png"))
