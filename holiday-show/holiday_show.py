"""Main controller (skeleton): presence detect -> greet -> listen/think/speak loop -> farewell."""
import os, sys, time, threading, subprocess
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "packs", "santa"))
import ai_backend
from variety import Variety
from sprite_player import SpritePlayer

E = lambda k, d: type(d)(os.environ.get(k, d))
MIC = E("SHOW_MIC_DEV", "plughw:CARD=CameraB409241,DEV=0"); CH = E("SHOW_MIC_CHANNELS", 4)
MIN_RMS, RATIO, CAP = E("SHOW_LISTEN_MIN_RMS", 110), E("SHOW_LISTEN_RATIO", 2.5), E("SHOW_LISTEN_FLOOR_CAP", 150)
END, MAXU, WAIT = E("SHOW_LISTEN_END", 0.6), E("SHOW_LISTEN_MAX", 4.0), E("SHOW_LISTEN_WAIT", 4.0)
MIN_FRAC, MIN_HITS, HOLD = E("SHOW_MIN_FRAC", 0.02), E("SHOW_MIN_HITS", 3), E("SHOW_HOLD", 12)
TURNS, COOLDOWN, REPLY_TO = E("SHOW_TALK_TURNS", 6), E("SHOW_COOLDOWN", 5), E("SHOW_REPLY_TIMEOUT", 8)


class Detector(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True); self.present = False; self.last = 0; self.frame = None
    def run(self):
        import cv2
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        mog = cv2.createBackgroundSubtractorMOG2(300, 32, False); k = np.ones((3, 3), np.uint8); hits = i = 0
        while True:
            ok, f = cap.read()
            if not ok: time.sleep(0.1); continue
            i += 1
            if i % 2: continue
            m = cv2.morphologyEx(mog.apply(f), cv2.MORPH_OPEN, k)
            hits = hits + 1 if (m > 0).mean() > MIN_FRAC else 0
            if hits >= MIN_HITS: self.last = time.time(); self.frame = f
            self.present = time.time() - self.last < HOLD and self.last > 0


def listen():
    """Energy-endpointed capture from the 4-ch mic; returns mono 16 kHz WAV bytes or None."""
    p = subprocess.Popen(["arecord", "-q", "-D", MIC, "-f", "S16_LE", "-r", "16000", "-c", str(CH), "-t", "raw"],
                         stdout=subprocess.PIPE)
    blk = 480 * CH * 2; pre, buf, noise = [], [], []; start = time.time(); spoke = False; last_voice = 0
    try:
        while True:
            a = np.frombuffer(p.stdout.read(blk), "<i2").reshape(-1, CH).mean(axis=1)
            if len(a) == 0: break
            rms = float(np.sqrt((a.astype(np.float64) ** 2).mean())); now = time.time()
            if now - start < 0.3: noise.append(rms); continue
            thr = max(min(np.median(noise or [0]), CAP) * RATIO, MIN_RMS)
            if rms > thr:
                if not spoke: buf = list(pre); spoke = True; t_sp = now
                last_voice = now
            (buf if spoke else pre).append(a); pre[:] = pre[-10:]
            if spoke and (now - last_voice > END or now - t_sp > MAXU): break
            if not spoke and now - start > WAIT: return None
    finally:
        p.kill()
    return ai_backend.pcm_to_wav(np.concatenate(buf).astype("<i2"), 16000) if buf else None


def converse(player, det, var, char, mode):
    history = []; silent = 0
    # fresh LLM-written opener, different every visit (canned 'nohear' if the LLM/TTS is slow)
    box = {}
    def first():
        t = ai_backend.opener(char, mode, var.avoid_hint(), var.temperature())
        if var.seen(t): t = ai_backend.opener(char, mode, var.avoid_hint(), 1.3)
        box["t"] = t; box["wav"] = ai_backend.speak(t, char)
    ft = threading.Thread(target=first, daemon=True); ft.start(); ft.join(REPLY_TO)
    if box.get("wav"): var.remember(box["t"]); player.say(box["wav"])
    for _ in range(TURNS):
        if not det.present: break
        player.set_state("listening"); wav = listen(); player.set_state("idle")
        if wav is None:
            silent += 1; player.say("nohear", var)
            if silent >= 2: break
            continue
        silent = 0; out = {}
        def reply():
            text = ai_backend.hear(wav)
            out["t"] = ai_backend.think(text, history[-6:], char, mode, var.avoid_hint(), var.temperature()) if text else None
            if out["t"] and var.seen(out["t"]):
                out["t"] = ai_backend.think(text, history[-6:], char, mode, var.avoid_hint(), 1.3)
            if out["t"]:
                var.remember(out["t"]); out["wav"] = ai_backend.speak(out["t"], char); history.extend(
                    [{"role": "user", "content": text}, {"role": "assistant", "content": out["t"]}])
        th = threading.Thread(target=reply, daemon=True); th.start()
        player.say("think", var)  # hides hear() latency
        if th.is_alive(): player.set_state("thinking")
        th.join(REPLY_TO); player.set_state("idle")
        if out.get("wav"): player.say(out["wav"])
        else: player.say("nohear", var)


def main():
    player = SpritePlayer(os.path.join(os.path.dirname(os.path.abspath(__file__)), "packs", "santa"))
    det = Detector(); det.start(); P = ai_backend.PERSONA
    var = Variety(P["characters"].keys(), P["modes"])
    while True:
        if det.present:
            char, mode = var.pick_character(), var.pick_mode(); player.set_character(char)
            player.say("greet", var); converse(player, det, var, char, mode); player.say("farewell", var); time.sleep(COOLDOWN)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
