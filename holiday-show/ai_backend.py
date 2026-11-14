"""Swappable hear / think / speak / see backends + code-enforced safety filters.
Nothing (frames, audio, transcripts) is written to disk."""
import io, json, os, re, wave, base64, random, urllib.request
import numpy as np

PACK = os.environ.get("SHOW_PACK", "santa")
_dir = os.path.dirname(os.path.abspath(__file__))
PERSONA = json.load(open(os.path.join(_dir, "packs", PACK, "characters.json")))
OLLAMA = os.environ.get("OLLAMA_URL", "http://lmstudio:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:12b-it-q8_0")
WHISPER = os.environ.get("WHISPER_URL", "http://127.0.0.1:8080/inference")
BLOCK = re.compile(r"\b(" + "|".join(map(re.escape, PERSONA["block"])) + r")\b", re.I)
VISION_BLOCK = re.compile(
    r"\b(faces?|smil\w*|eyes?|hair|skin|bod(?:y|ies)|aged?|years? old|young|old|pretty|"
    r"cute|beautiful|handsome|ugly|fat|thin|tall|short)\b", re.I)


def clean(text):
    """Strip think tags, stage directions, emoji; clamp to 2 sentences/220 chars; None if blocked."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"\*[^*]*\*|\([^)]*\)", "", text)
    text = re.sub(r"[^\x00-ɏ‘’“”]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = " ".join(re.split(r"(?<=[.!?])\s+", text)[:2])[:220].strip()
    if not text or BLOCK.search(text):
        return None
    return text


def _post(url, payload, headers=None, timeout=30):
    req = urllib.request.Request(url, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json", **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout).read()


def hear(wav_bytes):
    """POST WAV to local whisper-server (multipart)."""
    b = "----show"
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.wav\"\r\n"
            f"Content-Type: audio/wav\r\n\r\n").encode() + wav_bytes + \
           (f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\njson\r\n--{b}--\r\n").encode()
    req = urllib.request.Request(WHISPER, body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read()).get("text", "").strip()


def system_prompt(character, mode=None, avoid=""):
    c = PERSONA["characters"][character]
    extra = f" Optional flavor for this visit: {mode}" if mode else ""
    return f"{c['system']} You like {', '.join(c['likes'])}.{extra} {avoid}".strip()


def think(transcript, history=(), character="santa", mode=None, avoid="", temperature=1.0):
    msgs = [{"role": "system", "content": system_prompt(character, mode, avoid)}, *history,
            {"role": "user", "content": transcript}]
    try:
        r = json.loads(_post(f"{OLLAMA}/api/chat", {"model": MODEL, "messages": msgs, "stream": False,
                                                    "options": {"temperature": temperature}}))
        return clean(r["message"]["content"]) or random.choice(PERSONA["fallback"])
    except Exception:
        return random.choice(PERSONA["fallback"])


def opener(character, mode, avoid="", temperature=1.0):
    """Fresh, spoken first line for this visit (differs every time)."""
    return think("Say your first line to the child now.", (), character, mode, avoid, temperature)


def see(jpeg_bytes, character="santa"):
    """Two-hop vision: neutral caption of clothing/objects/mood only, filtered; then voiced via think()."""
    try:
        r = json.loads(_post(f"{OLLAMA}/api/chat", {"model": MODEL, "stream": False, "messages": [{
            "role": "user", "content": "In under 10 words, describe only clothing, objects, or mood. No faces or people's bodies.",
            "images": [base64.b64encode(jpeg_bytes).decode()]}]}))
        cap = clean(r["message"]["content"])
        if not cap or VISION_BLOCK.search(cap):
            return None
        line = think(f"Make one friendly remark about this scene: {cap}", character=character)
        return None if VISION_BLOCK.search(line) else line
    except Exception:
        return None


def pcm_to_wav(pcm_i16, rate=22050):
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(pcm_i16.astype("<i2").tobytes())
    return bio.getvalue()


def gemini_wav_to_22k(raw):
    """Fix trailing static: read ONLY the data chunk frames (drops C2PA/SynthID chunks),
    resample 24k->22.05k in memory, 50 ms fade-out, write well-formed WAV."""
    with wave.open(io.BytesIO(raw), "rb") as w:
        src_rate = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32)
    n_out = int(len(pcm) * 22050 / src_rate)
    out = np.interp(np.linspace(0, len(pcm) - 1, n_out), np.arange(len(pcm)), pcm)
    f = min(int(0.05 * 22050), len(out))
    if f:
        out[-f:] *= np.linspace(1, 0, f)
        out[-5:] = 0
    return pcm_to_wav(np.round(out).astype(np.int16))


def _speak_gemini(text, character="santa"):
    c = PERSONA["characters"][character]
    key = os.environ["GEMINI_API_KEY"]
    r = json.loads(_post(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        {"model": "gemini-3.8-flash-tts",
         "input": text,
         "annotations": [{"type": "speech_metadata", "style": c["style"]}],
         "response_format": {"type": "audio"},
         "generation_config": {"speech_config": [{"voice": c["voice"]}]}},
        {"x-goog-api-key": key}, timeout=20))
    # NOTE: response field path is unverified against the live API; adjust here if it differs.
    return gemini_wav_to_22k(base64.b64decode(r["audio"]["data"]))


def _speak_piper(text):
    import subprocess
    p = subprocess.run(["/opt/holiday-show/piper/piper", "-m", "/opt/holiday-show/voices/en_US-norman-medium.onnx",
                        "--output_raw"], input=text.encode(), capture_output=True, check=True)
    return pcm_to_wav(np.frombuffer(p.stdout, dtype="<i2"))


def speak(text, character="santa"):
    if os.environ.get("GEMINI_API_KEY"):
        try:
            return _speak_gemini(text, character)
        except Exception:
            pass
    return _speak_piper(text)
