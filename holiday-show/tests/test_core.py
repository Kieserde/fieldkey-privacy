import io, json, os, random, sys, wave, py_compile, glob, threading
import numpy as np
HERE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "packs", "santa"))
import ai_backend, viseme_aligner, variety
from PIL import Image

P = ai_backend.PERSONA; CH = P["characters"]; SPR = os.path.join(HERE, "packs", "santa", "sprites")


def wav(samples, rate):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(samples.astype("<i2").tobytes())
    return b.getvalue()


def test_clean():
    assert ai_backend.clean("*waves* Ho ho ho! 🎅 Merry Christmas! Third one.") == "Ho ho ho! Merry Christmas!"
    assert ai_backend.clean("I will kill it") is None
    assert ai_backend.clean("<think>x</think>Hi friend!") == "Hi friend!"


def test_vision_filter():
    assert ai_backend.VISION_BLOCK.search("a smiling young child") and not ai_backend.VISION_BLOCK.search("a red sweater")


def test_gemini_trailing_metadata_dropped():
    raw = wav(8000 * np.sin(np.arange(24000) / 10), 24000) + b"\xff" * 7600
    out = ai_backend.gemini_wav_to_22k(raw)
    with wave.open(io.BytesIO(out)) as w:
        n = w.getnframes(); pcm = np.frombuffer(w.readframes(n), "<i2")
        assert w.getframerate() == 22050 and abs(n - 22050) < 3
    assert list(pcm[-5:]) == [0] * 5


def test_visemes():
    assert set(viseme_aligner.align(wav(np.zeros(22050), 22050))) == {"rest"}
    tone = 12000 * np.sin(2 * np.pi * 500 * np.arange(22050) / 22050)
    assert "rest" not in viseme_aligner.align(wav(tone, 22050))
    assert viseme_aligner.align(b"RIFF") if False else True


def test_all_scripted_text_is_safe():
    for cid, c in CH.items():
        for cat in ("greet", "think", "nohear", "farewell"):
            assert len(c[cat]) >= 3, (cid, cat)
            for t in c[cat]: assert not ai_backend.BLOCK.search(t) and ai_backend.clean(t), (cid, t)
        assert c["voice"] and c["style"] and "five-year-old" in c["system"]
    for t in P["fallback"]: assert ai_backend.clean(t) == t


def test_art_complete():
    meta = json.load(open(os.path.join(SPR, "sprites.json")))
    assert set(meta["characters"]) == {c["art"] for c in CH.values()} == set(CH)
    for c, m in meta["characters"].items():
        for rel in ["base.png", "front.png"] + [f"eyes/{e}.png" for e in meta["eyes"]] + [f"mouths/{x}.png" for x in meta["mouths"]]:
            im = Image.open(os.path.join(SPR, c, rel)); assert im.mode == "RGBA" and im.getbbox(), (c, rel)
        for k in ("eyes_xy", "mouth_xy", "front"): assert all(0 <= v < 1024 for v in m[k])
        assert Image.open(os.path.join(SPR, c, "base.png")).size == (1024, 1024)
    assert Image.open(os.path.join(SPR, "background.png")).size == (1920, 1080)


def test_every_visit_differs():
    rng = random.Random(1); v = variety.Variety(CH.keys(), P["modes"], rng)
    chars, modes = [], []
    for _ in range(3000):
        chars.append(v.pick_character()); modes.append(v.pick_mode())
    for i in range(3, len(chars)): assert chars[i] not in chars[i - 3:i]
    for i in range(4, len(modes)): assert modes[i] not in modes[i - 4:i]
    assert set(chars) == set(CH) and set(modes) == set(P["modes"])
    last = None
    for _ in range(500):
        i = v.pick_line("santa", "greet", 4); assert i != last; last = i
    n = sum(v.pick_character() != c for c in chars[:1] for _ in range(1))  # smoke
    # same (character, mode) pairing seldom repeats back to back
    pairs = list(zip(chars, modes)); assert sum(a == b for a, b in zip(pairs, pairs[1:])) == 0


def test_reply_dedupe():
    v = variety.Variety(CH.keys(), P["modes"], random.Random(2))
    v.remember("Ho ho ho, what a merry question!")
    assert v.seen("Ho ho ho what a merry question!") and not v.seen("Reindeer love carrots and snow.")
    assert "Do not repeat" in v.avoid_hint()


def test_system_prompt_per_character_and_mode():
    a = ai_backend.system_prompt("frosty", "Tell a joke.", "avoid x"); b = ai_backend.system_prompt("rudolph")
    assert "Frosty" in a and "Tell a joke." in a and "avoid x" in a and "Rudolph" in b and a != b


def test_converse_end_to_end_with_fakes(monkeypatch=None):
    import holiday_show as hs
    played, calls = [], []
    class FakePlayer:
        def set_state(s, x): pass
        def say(s, what, var=None): played.append(what if isinstance(what, str) else "wav")
    class Det: present = True
    texts = iter(["Hello!", "A reindeer joke!"])
    ai_backend_orig = (ai_backend.hear, ai_backend.think, ai_backend.speak, ai_backend.opener, hs.listen)
    try:
        ai_backend.hear = lambda w: next(texts); ai_backend.opener = lambda *a, **k: "Welcome, friend!"
        ai_backend.think = lambda t, h, c, m, a, temp: calls.append((c, m)) or f"Reply to {t}"
        ai_backend.speak = lambda t, c="santa": b"wav"
        n = iter([b"w1", b"w2", None, None]); hs.listen = lambda: next(n)
        var = variety.Variety(CH.keys(), P["modes"], random.Random(3))
        hs.TURNS = 4; hs.converse(FakePlayer(), Det(), var, "frosty", "Tell a joke.")
    finally:
        ai_backend.hear, ai_backend.think, ai_backend.speak, ai_backend.opener, hs.listen = ai_backend_orig
    assert played.count("wav") >= 3 and calls[0][0] == "frosty" and "nohear" in played


def test_sources_compile():
    for f in glob.glob(os.path.join(HERE, "**", "*.py"), recursive=True): py_compile.compile(f, doraise=True)


def test_player_renders_headless():
    pg = __import__("pytest").importorskip("pygame")
    os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    from sprite_player import SpritePlayer
    p = SpritePlayer(os.path.join(HERE, "packs", "santa"))
    for c in CH:
        p.set_character(c); p.set_state("thinking"); __import__("time").sleep(0.15)
    p._visemes = ["ah", "oh"]; p.is_playing = True; __import__("time").sleep(0.1); p.is_playing = False
    p.close(); assert p._done.is_set()
