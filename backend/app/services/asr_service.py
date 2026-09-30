"""Speech-to-text using faster-whisper (CTranslate2-backed Whisper ASR)."""
import math
import threading
from typing import Tuple

import numpy as np
from faster_whisper import WhisperModel

from app.config import WHISPER_MODEL_SIZE

_whisper_model = None
_model_lock = threading.Lock()


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        with _model_lock:
            if _whisper_model is None:
                _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper_model


def extract_text_from_audio(audio: np.ndarray, sample_rate: int = 16000) -> Tuple[str, float]:
    if audio.size == 0:
        return "", 0.0

    model = _get_whisper_model()
    # VAD + resampling already handled in the pre-processing step, so it is
    # skipped here to avoid doing it twice.
    segments, _info = model.transcribe(audio, vad_filter=False)

    texts, probabilities = [], []
    for segment in segments:
        text = segment.text.strip()
        if text:
            texts.append(text)
            probabilities.append(min(1.0, math.exp(segment.avg_logprob)))

    recognized_text = " ".join(texts)
    confidence = sum(probabilities) / len(probabilities) if probabilities else 0.0
    return recognized_text, confidence
