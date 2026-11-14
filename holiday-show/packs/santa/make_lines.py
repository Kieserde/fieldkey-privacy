"""Pre-render canned lines for every character: python make_lines.py [char ...]"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import ai_backend
here = os.path.dirname(os.path.abspath(__file__))
chars = json.load(open(os.path.join(here, "characters.json")))["characters"]
for cid, c in chars.items():
    if len(sys.argv) > 1 and cid not in sys.argv[1:]: continue
    for cat in ("greet", "think", "nohear", "farewell"):
        d = os.path.join(here, "lines", cid, cat); os.makedirs(d, exist_ok=True)
        for i, text in enumerate(c[cat], 1):
            p = os.path.join(d, f"{i:02d}.wav")
            if not os.path.exists(p):
                open(p, "wb").write(ai_backend.speak(text, cid)); print("made", p)
