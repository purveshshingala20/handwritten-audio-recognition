"""Orchestrates pre-processing -> recognition -> post-processing."""
from pathlib import Path
from typing import Dict

from app.config import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS
from app.services import asr_service, audio_preprocessing, image_preprocessing, ocr_service, text_postprocessing


def get_file_category(extension: str) -> str:
    extension = extension.lower()
    if extension in IMAGE_EXTENSIONS:
        return "image"
    if extension in AUDIO_EXTENSIONS:
        return "audio"
    raise ValueError(f"Unsupported file extension: {extension}")


def run_pipeline(file_bytes: bytes, filename: str, model: str = "paddleocr") -> Dict:
    extension = Path(filename).suffix.lower()
    category = get_file_category(extension)

    if category == "image":
        processed_image = image_preprocessing.preprocess_image(file_bytes)
        raw_text, confidence = ocr_service.extract_text_from_image(processed_image, engine=model)
        model_used = model
    else:
        processed_audio, sample_rate = audio_preprocessing.preprocess_audio(file_bytes)
        raw_text, confidence = asr_service.extract_text_from_audio(processed_audio, sample_rate)
        model_used = "faster-whisper"

    cleaned_text = text_postprocessing.clean_text(raw_text)

    return {
        "file_type": category,
        "model_used": model_used,
        "recognized_text": cleaned_text,
        "confidence": round(float(confidence), 4),
    }
