# app/main.py
import io
import uuid
from typing import Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import torch

from .models import vqa_model, vqa_processor, device

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Хранилище сессий
VQA_SESSIONS: Dict[str, bytes] = {}
OCR_RESULTS: Dict[str, str] = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()


def ensure_image(file: UploadFile):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Ожидается файл изображения (png, jpg и т.п.). Проверьте тип файла.",
        )


@app.post("/api/vqa/init")
async def vqa_init(image: UploadFile = File(...)):
    """
    Загрузка изображения + первичное описание.
    Возвращает session_id и caption.
    """
    ensure_image(image)
    img_bytes = await image.read()
    image_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    session_id = str(uuid.uuid4())
    VQA_SESSIONS[session_id] = img_bytes

    prompt = "<image> Describe this image in detail."
    inputs = vqa_processor(text=prompt, images=image_pil, return_tensors="pt").to(device)
    with torch.no_grad():
        output_ids = vqa_model.generate(**inputs, max_new_tokens=128)
    caption = vqa_processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    return {"session_id": session_id, "caption": caption[(len(prompt)-len('<image>')):]}


@app.post("/api/vqa/ask")
async def vqa_ask(
    session_id: str = Form(...),
    question: str = Form(...),
):
    """
    Вопрос по уже загруженному изображению (без повторной загрузки).
    """
    if session_id not in VQA_SESSIONS:
        raise HTTPException(status_code=404, detail="Сессия не найдена или истекла")

    if not question.strip():
        raise HTTPException(status_code=400, detail="Вопрос не может быть пустым")

    img_bytes = VQA_SESSIONS[session_id]
    image_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    prompt = f"Answer the question based on the image <image>. Question: {question}"
    inputs = vqa_processor(text=prompt, images=image_pil, return_tensors="pt").to(device)

    with torch.no_grad():
        output_ids = vqa_model.generate(**inputs, max_new_tokens=128)
    answer = vqa_processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    return {"answer": answer[(len(prompt)-len('<image>')):]}


@app.post("/api/ocr")
async def ocr(
    image: UploadFile = File(...),
    max_length: int = Form(256),
):
    """
    OCR по изображению.
    Можно передавать max_length только числом.
    """
    ensure_image(image)

    if not isinstance(max_length, int):
        raise HTTPException(status_code=400, detail="max_length должен быть целым числом")
    if max_length <= 0 or max_length > 2048:
        raise HTTPException(status_code=400, detail="max_length должен быть в диапазоне 1–2048")

    img_bytes = await image.read()
    image_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    prompt = "Read the text on the image<image> and write it.\n Text on the image: "
    inputs = vqa_processor(text=prompt, images=image_pil, return_tensors="pt").to(device)

    with torch.no_grad():
        output_ids = vqa_model.generate(**inputs, max_new_tokens=128)
    text = vqa_processor.batch_decode(output_ids, skip_special_tokens=True)[0][(len(prompt) - len('<image>')):]

    ocr_id = str(uuid.uuid4())
    OCR_RESULTS[ocr_id] = text

    return {"ocr_id": ocr_id, "text": text}


@app.get("/api/ocr/{ocr_id}/download")
async def ocr_download(ocr_id: str):
    """
    Скачать результат OCR как текстовый файл.
    """
    if ocr_id not in OCR_RESULTS:
        raise HTTPException(status_code=404, detail="Результат не найден")

    text = OCR_RESULTS[ocr_id]
    filename = f"ocr_{ocr_id}.txt"
    path = f"./tmp/{filename}"
    with open(path, "w") as f:
        f.write(text)

    return FileResponse(
        path,
        media_type="text/plain",
        filename=filename,
    )
