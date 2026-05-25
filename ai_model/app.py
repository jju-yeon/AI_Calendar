import os

from fastapi import FastAPI
from pydantic import BaseModel

from predict_from_image import (
    predict_from_image,
    generate_calendar_json,
    ocr_image_to_text,
)

app = FastAPI()


class ImagePathRequest(BaseModel):
    image_path: str


class TextRequest(BaseModel):
    text: str


class MultiRequest(BaseModel):
    image_path: str
    prompt: str = ""


@app.get("/health")
def health():
    return {"success": True, "message": "AI model server is running"}


@app.post("/predict/image-path")
def predict_image_path(req: ImagePathRequest):
    if not os.path.exists(req.image_path):
        return {
            "success": False,
            "message": f"image file not found: {req.image_path}",
        }

    result = predict_from_image(req.image_path)

    return {
        "success": True,
        "message": result,
    }


@app.post("/predict/text")
def predict_text(req: TextRequest):
    text = req.text.strip()

    if not text:
        return {
            "success": False,
            "message": "text is required",
        }

    result = generate_calendar_json(text)

    return {
        "success": True,
        "message": result,
    }


@app.post("/predict/multi-path")
def predict_multi_path(req: MultiRequest):
    if not os.path.exists(req.image_path):
        return {
            "success": False,
            "message": f"image file not found: {req.image_path}",
        }

    ocr_text = ocr_image_to_text(req.image_path)

    combined_text = f"""
[사용자 입력]
{req.prompt}

[이미지 OCR 결과]
{ocr_text}
""".strip()

    result = generate_calendar_json(combined_text)

    return {
        "success": True,
        "message": result,
        "ocrText": ocr_text,
    }