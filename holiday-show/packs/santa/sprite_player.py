"""60 fps Pygame KMS/DRM renderer for all characters. IMPORTANT: pygame.init, mixer.init, set_mode and
flip must all run on ONE thread (the render thread) for the kmsdrm backend."""
import json, os, math, random, threading, time, io
from viseme_aligner import align, FPS

BLINK = [("blink_1", .04), ("blink_2", .04), ("blink_closed", .06), ("blink_1", .04)]


class SpritePlayer:
    def __init__(self, pack_dir, rng=None):
        self.pack = pack_dir; self.rng = rng or random.Random()
        self.state = "idle"; self.is_playing = False; self.character = None
        self._ready = threading.Event(); self._visemes = []; self._t0 = 0.0
        self.meta = json.load(open(os.path.join(pack_dir, "sprites", "sprites.json")))
        self.lines = {}  # (char, cat) -> sorted file list
        self._stop = threading.Event(); self._done = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()
        if not self._ready.wait(15): raise RuntimeError("display failed to start")

    def set_state(self, s): self.state = s
    def set_character(self, c): self.character = c

    def lines_for(self, char, cat):
        d = os.path.join(self.pack, "lines", char, cat)
        return sorted(os.path.join(d, f) for f in os.listdir(d)) if os.path.isdir(d) else []

    def say(self, what, variety=None):
        """what = canned category ('greet', ...) for the current character, or raw WAV bytes."""
        import pygame
        if isinstance(what, str):
            files = self.lines_for(self.character, what)
            if not files: return
            i = variety.pick_line(self.character, what, len(files)) if variety else self.rng.randrange(len(files))
            data = open(files[i], "rb").read()
        else:
            data = what
        self._visemes = align(data); snd = pygame.mixer.Sound(io.BytesIO(data)); self._t0 = time.time()
        self.is_playing = True; ch = snd.play()
        while ch and ch.get_busy(): time.sleep(0.02)
        self.is_playing = False

    def _run(self):
        try:
            self._render_loop()
        except Exception as e:
            if not self._stop.is_set():  # a real failure, not a requested shutdown
                import sys; print(f"[sprite_player] render loop crashed: {e!r}", file=sys.stderr)
            self._ready.set()
        finally:
            self._done.set()

    def close(self):
        """Stop the render thread and tear SDL down on that same thread."""
        self._stop.set(); self._done.wait(5)

    def _render_loop(self):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
        os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
        import pygame
        pygame.init(); pygame.mixer.init(22050, -16, 1, 1024)
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.FULLSCREEN
        screen = pygame.display.set_mode((0, 0), flags); pygame.mouse.set_visible(False)
        w, h = screen.get_size(); clock = pygame.time.Clock()
        sp = os.path.join(self.pack, "sprites"); scale = h * 0.92 / self.meta["characters"]["santa"]["canvas"]
        S = lambda im: pygame.transform.smoothscale(im, (max(1, int(im.get_width() * scale)), max(1, int(im.get_height() * scale))))
        load = lambda p: S(pygame.image.load(os.path.join(sp, p)).convert_alpha())
        bg = pygame.transform.smoothscale(pygame.image.load(os.path.join(sp, "background.png")).convert(), (w, h))
        cache = {}
        def sprites(c):
            if c not in cache:
                cache[c] = dict(base=load(f"{c}/base.png"), front=load(f"{c}/front.png"),
                                eyes={e: load(f"{c}/eyes/{e}.png") for e in self.meta["eyes"]},
                                mouths={m: load(f"{c}/mouths/{m}.png") for m in self.meta["mouths"]})
            return cache[c]
        font = pygame.font.Font(None, 44); next_blink = time.time() + 3; blink_i = None; blink_t = 0
        self._ready.set()
        while not self._stop.is_set():
            pygame.event.pump(); t = time.time(); screen.blit(bg, (0, 0))
            c = self.character
            if c:
                s, m = sprites(c), self.meta["characters"][c]
                ox = (w - s["base"].get_width()) // 2; oy = h - s["base"].get_height() + max(0, 2.5 * math.sin(2 * math.pi * .22 * t) + 3)
                P = lambda xy: (ox + xy[0] * scale, oy + xy[1] * scale)
                screen.blit(s["base"], (ox, oy))
                if blink_i is None and t >= next_blink: blink_i, blink_t = 0, t
                if blink_i is not None and t - blink_t >= BLINK[blink_i][1]:
                    blink_i += 1; blink_t = t
                    if blink_i >= len(BLINK): blink_i = None; next_blink = t + self.rng.uniform(3.5, 6)
                eye = BLINK[blink_i][0] if blink_i is not None else ("thinking" if self.state == "thinking" else "open")
                screen.blit(s["eyes"][eye], P(m["eyes_xy"]))
                mouth = "rest"
                if self.is_playing and self._visemes: mouth = self._visemes[min(int((t - self._t0) * FPS), len(self._visemes) - 1)]
                screen.blit(s["mouths"][mouth], P(m["mouth_xy"])); screen.blit(s["front"], P(m["front"]))
            if not self.is_playing and self.state in ("listening", "thinking"):
                col = (60, 200, 120) if self.state == "listening" else (240, 190, 60)
                name = (self.character or "Santa").replace("_", " ").title().split()[0]
                label = f"{name} is {self.state}..."; pulse = 7 + int(3 * math.sin(t * 5))
                txt = font.render(label, True, (255, 255, 255)); pw = txt.get_width() + 90
                pygame.draw.rect(screen, (0, 0, 0), (w // 2 - pw // 2, h - 96, pw, 60), border_radius=30)
                pygame.draw.circle(screen, col, (w // 2 - pw // 2 + 36, h - 66), pulse); screen.blit(txt, (w // 2 - pw // 2 + 62, h - 80))
            pygame.display.flip(); clock.tick(60)
        pygame.quit()
