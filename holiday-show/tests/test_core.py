import io, os, sys, struct, wave, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packs", "santa"))
import ai_backend, viseme_aligner


def wav(samples, rate):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(samples.astype("<i2").tobytes())
    return b.getvalue()


def test_clean():
    assert ai_backend.clean("*waves* Ho ho ho! 🎅 Merry Christmas! Third one.") == "Ho ho ho! Merry Christmas!"
    assert ai_backend.clean("I will kill it") is None


def test_gemini_trailing_metadata_dropped():
    t = np.arange(24000)
    raw = wav(8000 * np.sin(t / 10), 24000) + b"\xff" * 7600  # junk after data chunk
    out = ai_backend.gemini_wav_to_22k(raw)
    with wave.open(io.BytesIO(out)) as w:
        n = w.getnframes(); pcm = np.frombuffer(w.readframes(n), "<i2")
        assert w.getframerate() == 22050 and abs(n - 22050) < 3
    assert list(pcm[-5:]) == [0] * 5


def test_visemes():
    sil = viseme_aligner.align(wav(np.zeros(22050), 22050))
    assert set(sil) == {"rest"}
    tone = 12000 * np.sin(2 * np.pi * 500 * np.arange(22050) / 22050)
    assert "rest" not in viseme_aligner.align(wav(tone, 22050))
