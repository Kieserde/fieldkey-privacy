"""Makes every visit different: character rotation, per-visit mode/temperature, no-repeat line picking,
and reply de-duplication across visits."""
import random, re
from collections import deque


def words(t): return set(re.findall(r"[a-z']+", t.lower()))


def similar(a, b, th=0.6):
    A, B = words(a), words(b)
    return bool(A and B) and len(A & B) / len(A | B) >= th


class Variety:
    def __init__(self, characters, modes, rng=None, mem=40):
        self.chars, self.modes = list(characters), list(modes)
        self.rng = rng or random.Random()
        self.recent_chars = deque(maxlen=min(3, len(self.chars) - 1))
        self.recent_modes = deque(maxlen=min(4, len(self.modes) - 1))
        self.recent_lines = {}        # (char, cat) -> last index
        self.recent_replies = deque(maxlen=mem)

    def pick_character(self):
        c = self.rng.choice([x for x in self.chars if x not in self.recent_chars])
        self.recent_chars.append(c); return c

    def pick_mode(self):
        m = self.rng.choice([x for x in self.modes if x not in self.recent_modes])
        self.recent_modes.append(m); return m

    def pick_line(self, char, cat, n):
        """Index in [0,n) never equal to the previous pick for the same (char, cat)."""
        if n <= 1: return 0
        last = self.recent_lines.get((char, cat))
        i = self.rng.choice([x for x in range(n) if x != last]); self.recent_lines[(char, cat)] = i
        return i

    def temperature(self): return round(self.rng.uniform(0.8, 1.2), 2)

    def seen(self, reply): return any(similar(reply, r) for r in self.recent_replies)
    def remember(self, reply): self.recent_replies.append(reply)

    def avoid_hint(self, k=4):
        r = list(self.recent_replies)[-k:]
        return ("Do not repeat or closely paraphrase these earlier lines: " + " | ".join(r)) if r else ""
