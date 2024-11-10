# main.py
# from cache_utils import CacheServer
from io import BytesIO
import random
import logging
import os
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import torch
import numpy as np
import requests
from PIL import Image
import rembg
import xatlas
import uvicorn
import io
from PIL import Image

from tsr.system import TSR
from tsr.utils import remove_background, resize_foreground, save_video
from tsr.bake_texture import bake_texture
from dotenv import load_dotenv
import boto3

load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = FastAPI(title="3D Model Generation API")

API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {os.getenv('FLUX_API2')}"}
# CACHE_SERVER = CacheServer()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "dreamscapeassetbucket")
BLOB_STORAGE = boto3.client("s3")


def query(keyword):
    payload = {
        "inputs": f"a {keyword} against a plain gray background presented at slight angle to make it look like a 3d asset",
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content


def generate_image(keyword):
    image_bytes = query(keyword)
    image = Image.open(io.BytesIO(image_bytes))
    image.save(keyword + ".png", format="PNG")
    print(f"Image saved as {keyword}.png")


class ModelService:
    def __init__(
        self,
        device: str = "cuda:0",
        model_path: str = "stabilityai/TripoSR",
        chunk_size: int = 8192,
        output_dir: str = "output/",
    ):
        self.device = "cpu" if not torch.cuda.is_available() else device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize model
        logging.info("Initializing model...")
        self.model = TSR.from_pretrained(
            model_path, config_name="config.yaml", weight_name="model.ckpt"
        )
        self.model.renderer.set_chunk_size(chunk_size)
        self.model.to(self.device)

        # Initialize rembg session
        self.rembg_session = rembg.new_session()
        logging.info("Model service initialized successfully")

    async def process_image(
        self,
        image: Image.Image,
        object_name: str,
        foreground_ratio: float = 0.85,
        mc_resolution: int = 256,
        bake_texture: bool = False,
        texture_resolution: int = 0,
        render_video: bool = False,
        model_format: str = "obj",
        remove_bg: bool = True,
    ) -> dict:
        # Create output directory for this job
        job_dir = self.output_dir / object_name
        job_dir.mkdir(exist_ok=True)

        # Process image
        if remove_bg:
            image = remove_background(image, self.rembg_session)
            image = resize_foreground(image, foreground_ratio)
            image = np.array(image).astype(np.float32) / 255.0
            image = image[:, :, :3] * image[:, :, 3:4] + (1 - image[:, :, 3:4]) * 0.5
            image = Image.fromarray((image * 255.0).astype(np.uint8))
            image.save(job_dir / f"{object_name}.png")

        # Generate 3D model
        with torch.no_grad():
            scene_codes = self.model([image], device=self.device)

        # Render video if requested
        if render_video:
            render_images = self.model.render(
                scene_codes, n_views=30, return_type="pil"
            )
            for ri, render_image in enumerate(render_images[0]):
                render_image.save(job_dir / f"render_{ri:03d}.png")
            save_video(render_images[0], job_dir / "render.mp4", fps=30)

        # Extract mesh
        meshes = self.model.extract_mesh(
            scene_codes, bake_texture, resolution=mc_resolution
        )

        # Save mesh and texture
        mesh_path = job_dir / f"temp_{object_name}.{model_format}"
        if bake_texture:
            texture_path = job_dir / f"{object_name}.png"
            bake_output = bake_texture(
                meshes[0], self.model, scene_codes[0], texture_resolution
            )

            xatlas.export(
                str(mesh_path),
                meshes[0].vertices[bake_output["vmapping"]],
                bake_output["indices"],
                bake_output["uvs"],
                meshes[0].vertex_normals[bake_output["vmapping"]],
            )

            Image.fromarray((bake_output["colors"] * 255.0).astype(np.uint8)).transpose(
                Image.FLIP_TOP_BOTTOM
            ).save(texture_path)

            return {
                "mesh_path": str(mesh_path),
                "texture_path": str(texture_path),
                "render_path": str(job_dir / "render.mp4") if render_video else None,
            }
        else:
            meshes[0].export(str(mesh_path))
            return {
                "mesh_path": str(mesh_path),
                "render_path": str(job_dir / "render.mp4") if render_video else None,
            }


# Initialize model service at startup
model_service = None


@app.on_event("startup")
async def startup_event():
    global model_service
    model_service = ModelService()


@app.get("/generate/{object_name}")
async def generate_model(
    object_name: str,
    foreground_ratio: float = 0.85,
    mc_resolution: int = 256,
    bake_texture: bool = False,
    texture_resolution: int = 0,
    render_video: bool = False,
    model_format: str = "obj",
    remove_bg: bool = True,
):
    # embedding = CACHE_SERVER.getEmbedding(object_name)
    # print("--------------EMBEDDING--------------")
    # print(embedding)

    # cacheRes = CACHE_SERVER.get(embedding, object_name)
    # print("--------------CACHERES--------------")
    # print(cacheRes)

    # if cacheRes:
    #     return FileResponse(cacheRes, media_type="application/octet-stream")
    output_dir = "output/"
    object_dir = os.path.join(output_dir, object_name)

    # Check if folder with the object name exists
    if os.path.isdir(object_dir):
        return FileResponse(
            f"{object_dir}/{object_name}.obj",
            filename=f"{object_name}.obj",
        )
    try:
        # Read and convert image
        image_bytes = query(object_name)
        if not image_bytes:
            raise HTTPException(
                status_code=500, detail="Failed to generate image from keyword"
            )

        pil_image = Image.open(BytesIO(image_bytes))

        os.makedirs(f"output/{object_name}", exist_ok=True)
        temp_image_path = f"output/{object_name}/{object_name}.png"
        pil_image.save(temp_image_path, format="PNG")

        # Process image and generate model
        result = await model_service.process_image(
            pil_image,
            object_name,
            foreground_ratio,
            mc_resolution,
            bake_texture,
            texture_resolution,
            render_video,
            model_format,
            remove_bg,
        )

        logging.info("3D model generated!!!")

        import pymeshlab

        temp_obj_file_path = result["mesh_path"]
        obj_file_path = f"{object_dir}/{object_name}.obj"
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(temp_obj_file_path)
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=8000)
        ms.save_current_mesh(obj_file_path)

        logging.info("3d model smoothened!!!")

        with open(obj_file_path, "rb") as f:
            try:
                BLOB_STORAGE.upload_fileobj(f, S3_BUCKET_NAME, obj_file_path)

            except Exception as e:
                print(f"Error uploading file to S3: {e}")
                return None

        url = (
            f"https://dreamscapeassetbucket.s3.us-west-1.amazonaws.com/{obj_file_path}"
        )
        print("Uploaded file to S3.")
        # url = CACHE_SERVER.post(result["mesh_path"], embedding)

        return FileResponse(
            obj_file_path,
            filename=f"{object_name}.obj",
        )

    except Exception as e:
        logging.error("Error during model generation: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
