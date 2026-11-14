"""60 fps Pygame KMS/DRM renderer. IMPORTANT: pygame.init, mixer.init, set_mode and flip
must all run on ONE thread (the render thread) for the kmsdrm backend."""
import os, math, random, threading, time, io
from viseme_aligner import align, FPS


class SpritePlayer:
    def __init__(self, pack_dir):
        self.pack = pack_dir
        self.state = "idle"; self.is_playing = False
        self._ready = threading.Event(); self._sound = None; self._visemes = []; self._t0 = 0.0
        threading.Thread(target=self._render_loop, daemon=True).start()
        self._ready.wait(10)

    def set_state(self, s): self.state = s

    def say(self, category_or_wav):
        """Play a canned category (random line) or raw WAV bytes, blocking until done."""
        import pygame
        if isinstance(category_or_wav, str):
            d = os.path.join(self.pack, "lines", category_or_wav)
            data = open(os.path.join(d, random.choice(sorted(os.listdir(d)))), "rb").read()
        else:
            data = category_or_wav
        self._visemes = align(data)
        snd = pygame.mixer.Sound(io.BytesIO(data)); self._t0 = time.time()
        self.is_playing = True; ch = snd.play()
        while ch and ch.get_busy(): time.sleep(0.02)
        self.is_playing = False

    def _render_loop(self):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
        os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
        import pygame
        pygame.init(); pygame.mixer.init(22050, -16, 1, 1024)
        screen = pygame.display.set_mode((0, 0), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
        w, h = screen.get_size(); clock = pygame.time.Clock(); self._ready.set()
        sp = os.path.join(self.pack, "sprites")
        def img(p):
            f = os.path.join(sp, p); return pygame.image.load(f).convert_alpha() if os.path.exists(f) else None
        bg, base = img("background.png"), img("base.png")
        mouths = {m: img(f"mouths/{m}.png") for m in ("rest", "oh", "ah", "eh", "ee", "fv", "l_th")}
        font = pygame.font.Font(None, 40); next_blink = time.time() + 4
        while True:
            pygame.event.pump(); t = time.time()
            screen.fill((20, 10, 10))
            if bg: screen.blit(pygame.transform.smoothscale(bg, (w, h)), (0, 0))
            if base:
                sway = max(0, 2.5 * math.sin(2 * math.pi * 0.22 * t) + 3)
                screen.blit(base, ((w - base.get_width()) // 2, h - base.get_height() + sway))
                if self.is_playing and self._visemes:
                    i = min(int((t - self._t0) * FPS), len(self._visemes) - 1)
                    m = mouths.get(self._visemes[i])
                    if m: screen.blit(m, ((w - base.get_width()) // 2 + 430, h - base.get_height() + sway + 490))
            if not self.is_playing and self.state in ("listening", "thinking"):
                col = (60, 200, 120) if self.state == "listening" else (240, 190, 60)
                label = f"Santa is {self.state}..."
                pulse = 6 + int(3 * math.sin(t * 5))
                pygame.draw.rect(screen, (0, 0, 0), (w // 2 - 190, h - 96, 380, 60), border_radius=30)
                pygame.draw.circle(screen, col, (w // 2 - 150, h - 66), pulse)
                screen.blit(font.render(label, True, (255, 255, 255)), (w // 2 - 120, h - 80))
            pygame.display.flip(); clock.tick(60)
