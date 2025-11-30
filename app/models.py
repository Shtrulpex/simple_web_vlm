# app/models.py
import os
import torch
from transformers import (
    AutoProcessor,
    AutoModelForVision2Seq
)

DEVICE_ENV = os.getenv("DEVICE", "cpu")
if DEVICE_ENV == "gpu" and torch.cuda.is_available():
    device = torch.device("cuda")
    print(device)
else:
    device = torch.device("cpu")
    print(device)

VQA_MODEL_ID = os.getenv("VQA_MODEL_ID", "HuggingFaceTB/SmolVLM-256M-Instruct")
OCR_MODEL_ID = os.getenv("OCR_MODEL_ID", "microsoft/trocr-base-printed")

# Загрузка SmolVLM2
vqa_processor = AutoProcessor.from_pretrained(VQA_MODEL_ID)
vqa_model = AutoModelForVision2Seq.from_pretrained(VQA_MODEL_ID)
vqa_model.to(device)
vqa_model.eval()
