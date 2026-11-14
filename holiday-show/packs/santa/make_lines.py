"""Pre-render canned lines: python make_lines.py  (needs ai_backend.speak working)."""
import os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import ai_backend
here = os.path.dirname(os.path.abspath(__file__))
n = collections.Counter()
for ln in open(os.path.join(here, "lines.txt")):
    if "|" not in ln: continue
    cat, text = ln.strip().split("|", 1)
    n[cat] += 1
    d = os.path.join(here, "lines", cat); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"{n[cat]:02d}.wav"), "wb").write(ai_backend.speak(text))
