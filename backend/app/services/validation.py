"""Upload validation: file existence, type, and size checks."""
from pathlib import Path

from app.config import ALLOWED_EXTENSIONS, IMAGE_MODELS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from app.errors import ApiError


def validate_file(filename: str, contents: bytes, model: str) -> str:
    """Validates an uploaded file and returns its lowercase extension."""
    if not filename or not filename.strip():
        raise ApiError("File must be provided.")

    if not contents:
        raise ApiError(f"Uploaded file '{filename}' is empty.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ApiError(
            f"Unsupported file type '{extension}' for '{filename}'. "
            "Allowed types: PNG, JPG, JPEG, BMP, TIFF, MP3, M4A, WAV, FLAC."
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise ApiError(f"File '{filename}' exceeds the {MAX_FILE_SIZE_MB}MB size limit.")

    if model not in IMAGE_MODELS:
        raise ApiError(f"Unsupported model '{model}'. Allowed models: {', '.join(sorted(IMAGE_MODELS))}.")

    return extension
