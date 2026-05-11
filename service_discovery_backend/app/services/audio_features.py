from __future__ import annotations

from typing import Dict
import io
import wave
import numpy as np


def extract_wav_features(content: bytes) -> Dict[str, float]:
    """Extract simple acoustic features from a WAV file.

    The implementation is dependency-light so the backend can run on student
    laptops. For MP3/M4A, the endpoint still accepts the file but returns a
    warning because Python's standard library cannot decode those formats.
    """
    try:
        with wave.open(io.BytesIO(content), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
            sample_width = wav.getsampwidth()
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            n_frames = wav.getnframes()
        dtype = np.int16 if sample_width == 2 else np.uint8
        audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        if sample_width == 2:
            audio = audio / 32768.0
        else:
            audio = (audio - 128.0) / 128.0
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)
        duration = n_frames / float(sample_rate) if sample_rate else 0.0
        rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        zero_cross = float(np.mean(np.abs(np.diff(np.signbit(audio))))) if audio.size > 1 else 0.0
        return {
            "duration_seconds": round(duration, 4),
            "sample_rate": float(sample_rate),
            "channels": float(channels),
            "rms": round(rms, 4),
            "peak": round(peak, 4),
            "zero_cross_rate": round(zero_cross, 4),
            "warning": "",
        }
    except Exception:
        return {
            "duration_seconds": 0.0,
            "sample_rate": 0.0,
            "channels": 0.0,
            "rms": 0.0,
            "peak": 0.0,
            "zero_cross_rate": 0.0,
            "warning": "Only uncompressed WAV files can be decoded by this lightweight local prototype.",
        }
