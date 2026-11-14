"""Pure-NumPy acoustic viseme scheduler: 30 fps mouth shapes from 16-bit mono PCM."""
import io
import wave
import numpy as np

FPS = 30


def _load(src):
    w = wave.open(io.BytesIO(src) if isinstance(src, (bytes, bytearray)) else src, "rb")
    with w:
        rate, n = w.getframerate(), w.getnframes()
        pcm = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32)
        if w.getnchannels() > 1:
            pcm = pcm.reshape(-1, w.getnchannels()).mean(axis=1)
    return pcm, rate


def classify(norm_rms, zcr, centroid):
    if norm_rms < 0.08:
        return "rest"
    if zcr > 0.14 and norm_rms < 0.45:
        return "fv"
    if centroid > 2200:
        return "ee"
    if centroid > 1450:
        return "l_th" if norm_rms < 0.35 else "eh"
    if centroid < 1050 and norm_rms > 0.30:
        return "oh"
    if norm_rms > 0.55:
        return "ah"
    return "eh"


def align(src):
    """Return list of viseme names, one per 1/30 s block. src: path or WAV bytes."""
    pcm, rate = _load(src)
    blk = rate // FPS
    n = len(pcm) // blk
    if n == 0:
        return []
    blocks = pcm[: n * blk].reshape(n, blk)
    rms = np.sqrt((blocks ** 2).mean(axis=1))
    peak = np.percentile(rms, 95) or 1.0
    norm = np.clip(rms / peak, 0, 1.5)
    signs = np.signbit(blocks)
    zcr = (signs[:, 1:] != signs[:, :-1]).sum(axis=1) / blk
    mag = np.abs(np.fft.rfft(blocks, axis=1))
    freqs = np.fft.rfftfreq(blk, 1.0 / rate)
    cent = (mag * freqs).sum(axis=1) / np.maximum(mag.sum(axis=1), 1e-9)
    out = [classify(a, b, c) for a, b, c in zip(norm, zcr, cent)]
    # 1-frame smoothing: drop isolated flicker
    for i in range(1, n - 1):
        if out[i - 1] == out[i + 1] != out[i]:
            out[i] = out[i - 1]
    return out
