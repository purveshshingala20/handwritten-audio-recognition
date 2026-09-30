"""Central configuration for the recognition service."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / "storage" / "recognition.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
TESSERACT_CMD = os.getenv("TESSERACT_CMD") or None

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".flac"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | AUDIO_EXTENSIONS

IMAGE_MODELS = {"paddleocr", "tesseract"}
