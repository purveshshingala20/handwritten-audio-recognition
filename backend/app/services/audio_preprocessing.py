"""Audio pre-processing pipeline: decode/resample -> noise reduction -> VAD.

Decoding + resampling is done with PyAV (bundles its own ffmpeg libraries, so
no system ffmpeg install is required). Noise reduction uses spectral-gating
(`noisereduce`). Voice Activity Detection uses Silero VAD to keep only the
speech segments before they are handed to the ASR model.
"""
import io
from typing import Tuple

import av
import noisereduce as nr
import numpy as np
import torch
from silero_vad import get_speech_timestamps, load_silero_vad

TARGET_SAMPLE_RATE = 16000

_vad_model = None


def _get_vad_model():
    global _vad_model
    if _vad_model is None:
        _vad_model = load_silero_vad()
    return _vad_model


def decode_and_resample(file_bytes: bytes) -> np.ndarray:
    """Decodes any supported audio container to mono float32 PCM at 16kHz."""
    container = av.open(io.BytesIO(file_bytes))
    if not container.streams.audio:
        raise ValueError("No audio stream found in file.")
    stream = container.streams.audio[0]

    resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=TARGET_SAMPLE_RATE)

    chunks = []
    for packet in container.demux(stream):
        try:
            frames = packet.decode()
        except av.error.InvalidDataError:
            # Tolerate a corrupt/truncated trailing packet (common in
            # real-world exports, e.g. WhatsApp audio cut off mid-frame)
            # instead of discarding everything decoded so far.
            continue
        for frame in frames:
            for resampled_frame in resampler.resample(frame):
                chunks.append(resampled_frame.to_ndarray())
    container.close()

    if not chunks:
        raise ValueError("Unable to decode any audio frames from file.")

    pcm = np.concatenate(chunks, axis=1).flatten()
    audio = pcm.astype(np.float32) / 32768.0
    return audio


def reduce_noise(audio: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    if audio.size == 0:
        return audio
    return nr.reduce_noise(y=audio, sr=sample_rate).astype(np.float32)


def apply_vad(audio: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    if audio.size == 0:
        return audio
    model = _get_vad_model()
    tensor = torch.from_numpy(audio)
    timestamps = get_speech_timestamps(tensor, model, sampling_rate=sample_rate)
    if not timestamps:
        # No speech detected by VAD: fall back to the full (denoised) audio
        # rather than returning nothing, so the ASR step still gets a shot.
        return audio
    segments = [audio[t["start"]:t["end"]] for t in timestamps]
    return np.concatenate(segments)


def preprocess_audio(file_bytes: bytes) -> Tuple[np.ndarray, int]:
    audio = decode_and_resample(file_bytes)
    denoised = reduce_noise(audio)
    speech_only = apply_vad(denoised)
    return speech_only, TARGET_SAMPLE_RATE
