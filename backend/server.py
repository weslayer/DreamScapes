from fastapi import FastAPI
import requests
import io
from PIL import Image
import os
from dotenv import load_dotenv
import torch
from tsr.system import TSR
from tsr.utils import remove_background, resize_foreground
import numpy as np
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
headers = {"Authorization": f"Bearer {os.getenv('FLUX_API')}"}

device = "cuda" if torch.cuda.is_available() else "cpu"
model = TSR.from_pretrained("stabilityai/TripoSR", config_name="config.yaml", weight_name="model.ckpt")
model.to(device)

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.content

@app.get("/text_to_image/{object}")
async def text_to_image(object: str):
    image_bytes = query({
        "inputs": f"a {object} against a plain gray background presented at slight angle to emphasize the depth of each layer and make it look like a 3d asset",
    })
    image = Image.open(io.BytesIO(image_bytes))
    image.save(f"{object}.png", format="PNG")
    convert_to_3d(f"{object}.png")

def convert_to_3d(image_path):
     # Load and preprocess the image
    image = Image.open(image_path).convert("RGB")
    image = remove_background(image)
    image = resize_foreground(image, 0.85)
    image = np.array(image).astype(np.float32) / 255.0
    image = image[:, :, :3] * image[:, :, 3:4] + (1 - image[:, :, 3:4]) * 0.5
    image = Image.fromarray((image * 255.0).astype(np.uint8))
    logger.info("HERER!!!1")
    # Generate 3D model
    with torch.no_grad():
        scene_codes = model([image], device=device)
    logger.info("HERERE222")
    # Extract mesh
    meshes = model.extract_mesh(scene_codes, has_vertex_color=True, resolution=256)
    logger.info("HERHERE333")
    # Save the mesh
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    mesh_path = os.path.join(output_dir, "generated_3d_model.obj")
    meshes[0].export(mesh_path)

# uvicorn server:app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
