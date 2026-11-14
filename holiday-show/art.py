"""Procedural, license-free art for every character (no image credits, fully reproducible).
Layers per character: back (body+head) -> eyes -> mouth -> front (mustache, nose, hat brim...).
Run: python art.py  -> packs/santa/sprites/<char>/... + background.png + sprites.json"""
import json, math, os
from PIL import Image, ImageDraw, ImageFilter

S, K = 1024, 2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packs", "santa", "sprites")
MOUTHS = ["rest", "oh", "ah", "eh", "ee", "fv", "l_th"]
EYES = ["open", "blink_1", "blink_2", "blink_closed", "thinking", "squint"]
CAVITY, TONGUE, TEETH, INK = (74, 12, 26), (222, 92, 104), (252, 251, 246), (40, 24, 24)


class C:
    def __init__(self, w=S, h=S):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def _p(self, pts): return [(x * K, y * K) for x, y in pts]
    def e(self, cx, cy, rx, ry, fill, ol=None, lw=6):
        self.d.ellipse([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K], fill=fill, outline=ol, width=lw * K if ol else 0)
    def poly(self, pts, fill, ol=None, lw=6):
        self.d.polygon(self._p(pts), fill=fill, outline=ol, width=lw * K if ol else 0)
        if ol: self.d.line(self._p(pts + [pts[0]]), fill=ol, width=lw * K, joint="curve")
    def rr(self, x0, y0, x1, y1, r, fill, ol=None, lw=6):
        self.d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], r * K, fill=fill, outline=ol, width=lw * K if ol else 0)
    def line(self, pts, w, fill): self.d.line(self._p(pts), fill=fill, width=int(w * K), joint="curve")
    def arc(self, cx, cy, rx, ry, a0, a1, w, fill):
        self.d.arc([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K], a0, a1, fill=fill, width=int(w * K))
    def out(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def shade(c, f): return tuple(max(0, min(255, int(v * f))) for v in c[:3])


# ---- character bodies: each returns (back, front) canvases --------------------------------
def santa(b, f):
    RED, WH, SK = (206, 32, 40), (250, 250, 250), (246, 204, 178)
    b.rr(190, 640, 834, 1120, 210, RED, shade(RED, .6)); b.rr(470, 700, 554, 1100, 20, WH, (200, 200, 200), 4)
    b.rr(190, 900, 834, 965, 12, (30, 30, 34)); b.rr(462, 890, 562, 975, 12, (240, 196, 60), (150, 110, 20), 5)
    b.e(215, 860, 60, 70, WH, (200, 200, 200), 4); b.e(809, 860, 60, 70, WH, (200, 200, 200), 4)
    b.e(512, 420, 158, 150, SK, shade(SK, .7))
    b.poly([(346, 360), (678, 360), (650, 250), (610, 160), (690, 120), (736, 196), (700, 130)][:4] + [(512, 90)], RED, shade(RED, .6))
    b.e(512, 590, 178, 150, WH, (205, 205, 205), 5); b.e(366, 480, 34, 100, WH, (205, 205, 205), 5); b.e(658, 480, 34, 100, WH, (205, 205, 205), 5)
    f.rr(318, 322, 706, 402, 40, WH, (205, 205, 205), 5); f.e(512, 82, 44, 44, WH, (205, 205, 205), 5)
    f.e(458, 508, 62, 32, WH, (200, 200, 200), 5); f.e(566, 508, 62, 32, WH, (200, 200, 200), 5)
    f.e(512, 478, 28, 24, (236, 150, 140), shade((236, 150, 140), .7), 4)
    for sx in (-1, 1): f.arc(512 + sx * 62, 372, 46, 24, 200 if sx < 0 else 340, 340 if sx < 0 else 200 + 360, 14, WH)
    return dict(eye=(512, 418, 62, 22), mouth=(512, 548, 120), lid=SK, sclera=True)


def mrs_claus(b, f):
    RED, WH, SK, HAIR = (196, 40, 52), (250, 250, 250), (246, 206, 182), (214, 214, 224)
    b.rr(185, 540, 839, 1120, 220, RED, shade(RED, .6)); b.poly([(400, 640), (624, 640), (700, 1100), (324, 1100)], WH, (210, 210, 210), 4)
    b.rr(200, 790, 824, 830, 10, (30, 120, 70)); b.e(215, 860, 58, 66, SK, shade(SK, .7)); b.e(809, 860, 58, 66, SK, shade(SK, .7))
    b.e(512, 215, 90, 82, HAIR, shade(HAIR, .7)); b.e(512, 420, 158, 150, HAIR, shade(HAIR, .7))
    b.e(512, 440, 138, 132, SK, shade(SK, .7))
    f.poly([(348, 360), (676, 360), (640, 250), (512, 200), (386, 250)], HAIR, shade(HAIR, .7))
    b.poly([(400, 320), (624, 320), (580, 230), (444, 230)], (30, 130, 70), (18, 80, 44))
    f.e(512, 200, 50, 40, (206, 40, 52), shade(RED, .6), 5)
    for dx in (-62, 62):
        f.e(512 + dx, 418, 50, 44, (255, 255, 255, 40), (150, 110, 40), 7)
    f.line([(562, 418), (462, 418)], 6, (150, 110, 40))
    f.e(512, 478, 20, 17, (240, 160, 150), shade((240, 160, 150), .7), 4); f.e(430, 505, 22, 14, (255, 150, 150, 130)); f.e(594, 505, 22, 14, (255, 150, 150, 130))
    return dict(eye=(512, 420, 62, 22), mouth=(512, 540, 100), lid=SK, sclera=True)


def elf(b, f, hat=(34, 150, 74), alt=(206, 32, 40), name="jingle"):
    SK = (248, 214, 186)
    b.poly([(320, 560), (704, 560), (790, 1100), (234, 1100)], hat, shade(hat, .6)); b.rr(320, 560, 704, 620, 20, alt, shade(alt, .6))
    b.rr(250, 900, 774, 950, 10, (60, 40, 30)); b.rr(470, 892, 554, 958, 10, (240, 196, 60), (150, 110, 20), 5)
    b.e(300, 840, 52, 60, SK, shade(SK, .7)); b.e(724, 840, 52, 60, SK, shade(SK, .7))
    b.poly([(364, 440), (270, 360), (366, 400)], SK, shade(SK, .7)); b.poly([(660, 440), (754, 360), (658, 400)], SK, shade(SK, .7))
    b.e(512, 450, 152, 144, SK, shade(SK, .7))
    b.poly([(352, 380), (672, 380), (620, 250), (700, 120), (730, 90), (560, 190), (450, 240)][:3] + [(740, 80), (500, 200)], hat, shade(hat, .6))
    f.rr(340, 345, 684, 410, 30, alt, shade(alt, .6)); f.e(740, 84, 28, 28, (240, 200, 70), (150, 110, 20), 5)
    f.e(512, 495, 15, 12, (240, 160, 150), shade((240, 160, 150), .7), 3); f.e(420, 515, 26, 16, (255, 140, 140, 130)); f.e(604, 515, 26, 16, (255, 140, 140, 130))
    return dict(eye=(512, 450, 64, 26), mouth=(512, 548, 130), lid=SK, sclera=True)


def elf_holly(b, f): return elf(b, f, (230, 232, 236), (206, 32, 40), "holly")


def rudolph(b, f):
    BR, CR = (150, 98, 58), (240, 218, 180)
    b.rr(250, 580, 774, 1120, 200, BR, shade(BR, .6)); b.e(512, 880, 130, 190, CR, shade(CR, .8))
    for sx in (-1, 1):
        x = 512 + sx * 120
        b.line([(x, 300), (x + sx * 70, 190), (x + sx * 60, 90)], 22, (110, 76, 46)); b.line([(x + sx * 62, 190), (x + sx * 140, 160)], 18, (110, 76, 46))
        b.line([(x + sx * 50, 132), (x + sx * 110, 80)], 16, (110, 76, 46))
        b.e(512 + sx * 170, 380, 44, 68, BR, shade(BR, .6)); b.e(512 + sx * 170, 385, 22, 42, (234, 170, 150))
    b.e(512, 450, 170, 160, BR, shade(BR, .6)); b.e(512, 540, 110, 84, CR, shade(CR, .8))
    f.e(512, 520, 46, 40, (232, 28, 36), (140, 10, 20), 6); f.e(498, 506, 12, 9, (255, 190, 190))
    f.e(512, 520, 90, 78, (255, 40, 40, 40))
    return dict(eye=(512, 420, 74, 26), mouth=(512, 600, 110), lid=BR, sclera=True)


def frosty(b, f):
    WH = (250, 252, 255); ol = (180, 196, 214)
    b.e(512, 880, 270, 220, WH, ol, 6); b.e(512, 640, 200, 170, WH, ol, 6)
    b.line([(330, 700), (170, 600), (130, 520)], 18, (110, 76, 46)); b.line([(694, 700), (854, 600), (894, 520)], 18, (110, 76, 46))
    b.line([(170, 600), (130, 610)], 12, (110, 76, 46)); b.line([(854, 600), (894, 610)], 12, (110, 76, 46))
    b.e(512, 400, 160, 150, WH, ol, 6)
    for y in (730, 800, 870): f.e(512, y, 16, 16, (30, 30, 34))
    f.rr(340, 548, 684, 600, 22, (210, 40, 50), (130, 20, 30), 5); f.rr(580, 585, 650, 740, 20, (190, 34, 44), (130, 20, 30), 5)
    f.poly([(512, 425), (630, 440), (512, 462)], (244, 140, 40), (170, 90, 20), 4)
    f.rr(300, 270, 724, 300, 8, (30, 30, 34)); f.rr(372, 120, 652, 280, 14, (30, 30, 34)); f.rr(372, 238, 652, 266, 4, (150, 40, 50))
    return dict(eye=(512, 395, 58, 18), mouth=(512, 505, 110), lid=WH, sclera=False)


def gingerbread(b, f):
    GB, IC = (176, 108, 52), (255, 252, 244)
    b.rr(270, 560, 754, 1120, 120, GB, shade(GB, .6)); b.rr(70, 640, 340, 740, 50, GB, shade(GB, .6)); b.rr(684, 640, 954, 740, 50, GB, shade(GB, .6))
    b.e(512, 410, 200, 190, GB, shade(GB, .6)); b.e(512, 410, 180, 170, None, IC, 10)
    b.line([(290, 700), (734, 700)], 12, IC)
    for y, c in ((800, (220, 50, 60)), (890, (40, 160, 80)), (980, (240, 190, 60))): f.e(512, y, 28, 28, c, shade(c, .6), 4)
    f.e(400, 480, 22, 14, (255, 140, 140, 150)); f.e(624, 480, 22, 14, (255, 140, 140, 150))
    return dict(eye=(512, 380, 66, 22), mouth=(512, 480, 120), lid=GB, sclera=False)


CHARACTERS = {"santa": santa, "mrs_claus": mrs_claus, "elf_jingle": elf, "elf_holly": elf_holly,
              "rudolph": rudolph, "frosty": frosty, "gingerbread": gingerbread}


# ---- faces ----------------------------------------------------------------------------------
def eyes_img(p, state):
    c = C(); cx, cy, dx, r = p["eye"][0], p["eye"][1], p["eye"][2], p["eye"][3]
    for sx in (-1, 1):
        x = cx + sx * dx
        if p["sclera"]:
            rx, ry = r * 1.1, r * 1.25
            c.e(x, cy, rx, ry, (255, 255, 255), (90, 70, 70), 4)
            px, py = {"thinking": (x + sx * 0 + 8, cy - 11), "squint": (x, cy)}.get(state, (x, cy + 2))
            c.e(px, py, r * .62, r * .66, (70, 44, 28)); c.e(px, py, r * .32, r * .34, (10, 10, 12)); c.e(px - 5, py - 6, 5, 5, (255, 255, 255))
        else:
            px, py = (x + 6, cy - 12) if state == "thinking" else (x, cy)
            c.e(px, py, r * .8, r * .85, (14, 14, 18)); c.e(px - 5, py - 6, 5, 5, (255, 255, 255))
        cover = {"blink_1": .4, "blink_2": .75, "blink_closed": 1.1, "squint": .45}.get(state, 0)
        if cover:
            top, h = cy - r * 1.4, r * 2.8
            c.rr(x - r * 1.5, top, x + r * 1.5, top + h * min(cover, 1) if cover < 1.05 else cy + r * 1.5, 10, p["lid"])
            if cover >= 1:
                c.arc(x, cy - 6, r * 1.1, r * .6, 20, 160, 7, INK)
            elif state == "squint":
                c.arc(x, cy + 6, r * 1.1, r * .55, 200, 340, 7, INK)
    return c.out()


def mouth_img(p, m):
    c = C(); x, y, w = p["mouth"]
    if m == "rest":
        c.arc(x, y - w * .12, w * .38, w * .2, 20, 160, 8, INK)
    elif m == "oh":
        c.e(x, y, w * .17, w * .2, CAVITY, INK, 5); c.e(x, y + w * .08, w * .1, w * .07, TONGUE)
    elif m == "ah":
        c.e(x, y + 4, w * .26, w * .28, CAVITY, INK, 5); c.e(x, y + w * .16, w * .17, w * .1, TONGUE)
    elif m == "eh":
        c.e(x, y, w * .34, w * .14, CAVITY, INK, 5); c.e(x, y + w * .07, w * .2, w * .05, TONGUE)
    elif m == "ee":
        c.rr(x - w * .4, y - w * .09, x + w * .4, y + w * .13, int(w * .1), CAVITY, INK, 5); c.rr(x - w * .36, y - w * .08, x + w * .36, y - w * .01, 6, TEETH)
    elif m == "fv":
        c.rr(x - w * .34, y - w * .06, x + w * .34, y + w * .1, int(w * .08), CAVITY, INK, 5); c.rr(x - w * .3, y - w * .05, x + w * .3, y + w * .02, 5, TEETH)
        c.rr(x - w * .3, y + w * .0, x + w * .3, y + w * .09, 8, (236, 140, 140))
    elif m == "l_th":
        c.e(x, y, w * .3, w * .13, CAVITY, INK, 5); c.rr(x - w * .22, y - w * .1, x + w * .22, y - w * .02, 5, TEETH); c.e(x, y + w * .08, w * .12, w * .06, TONGUE)
    return c.out()


def bbox_of(imgs, pad=6):
    bb = None
    for im in imgs:
        b = im.getbbox()
        if b: bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    return (max(0, bb[0] - pad), max(0, bb[1] - pad), min(S, bb[2] + pad), min(S, bb[3] + pad))


def build_character(name):
    d = os.path.join(OUT, name); os.makedirs(os.path.join(d, "eyes"), exist_ok=True); os.makedirs(os.path.join(d, "mouths"), exist_ok=True)
    b, f = C(), C(); p = CHARACTERS[name](b, f)
    back, front = b.out(), f.out()
    eyes = {s: eyes_img(p, s) for s in EYES}; mouths = {m: mouth_img(p, m) for m in MOUTHS}
    back.save(os.path.join(d, "base.png")); meta = {"canvas": S, "face": p["mouth"][:2]}
    fb = front.getbbox(); front.crop(fb).save(os.path.join(d, "front.png")); meta["front"] = fb[:2]
    eb = bbox_of(eyes.values()); meta["eyes_xy"] = eb[:2]
    for s, im in eyes.items(): im.crop(eb).save(os.path.join(d, "eyes", f"{s}.png"))
    mb = bbox_of(mouths.values()); meta["mouth_xy"] = mb[:2]
    for m, im in mouths.items(): im.crop(mb).save(os.path.join(d, "mouths", f"{m}.png"))
    return meta


def background(w=1920, h=1080):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h; d.line([(0, y), (w, y)], fill=(int(58 + 40 * t), int(26 + 18 * t), int(30 + 14 * t)))
    d.rectangle([0, int(h * .78), w, h], fill=(96, 62, 40))
    for x in range(0, w, 140): d.line([(x, int(h * .78)), (x - 80, h)], fill=(76, 48, 30), width=4)
    wx0, wy0 = 120, 170  # window with snowy night
    d.rounded_rectangle([wx0, wy0, wx0 + 420, wy0 + 520], 24, fill=(20, 34, 78), outline=(120, 80, 50), width=18)
    import random; r = random.Random(7)
    for _ in range(70):
        x, y = r.randint(wx0 + 14, wx0 + 406), r.randint(wy0 + 14, wy0 + 500); d.ellipse([x, y, x + 5, y + 5], fill=(240, 244, 255))
    d.polygon([(wx0, wy0 + 520), (wx0 + 140, wy0 + 440), (wx0 + 280, wy0 + 500), (wx0 + 420, wy0 + 430), (wx0 + 420, wy0 + 520)], fill=(232, 240, 250))
    d.line([(wx0 + 210, wy0), (wx0 + 210, wy0 + 520)], fill=(120, 80, 50), width=12); d.line([(wx0, wy0 + 260), (wx0 + 420, wy0 + 260)], fill=(120, 80, 50), width=12)
    fx = w - 560  # fireplace
    d.rectangle([fx, 380, fx + 440, int(h * .78)], fill=(120, 70, 60), outline=(70, 40, 34), width=10); d.rounded_rectangle([fx + 70, 480, fx + 370, int(h * .78)], 60, fill=(20, 10, 10))
    for i, c in enumerate(((255, 140, 30), (255, 200, 60), (255, 90, 20))): d.polygon([(fx + 150 + i * 30, int(h * .78)), (fx + 190 + i * 30, 560 + i * 40), (fx + 240 + i * 30, int(h * .78))], fill=c)
    for i, c in enumerate(((210, 40, 50), (40, 150, 80), (240, 190, 60))):
        x = fx + 40 + i * 140; d.polygon([(x, 380), (x + 40, 340), (x + 80, 380)], fill=c)
    pts = [(x, 40 + int(46 * math.sin(x / 170))) for x in range(0, w, 12)]  # garland + lights
    d.line(pts, fill=(30, 110, 60), width=22)
    for i, (x, y) in enumerate(pts[::6]): d.ellipse([x - 9, y + 12, x + 9, y + 30], fill=[(255, 70, 70), (255, 220, 80), (90, 200, 255), (120, 255, 140)][i % 4])
    return im.filter(ImageFilter.GaussianBlur(1.2))


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {n: build_character(n) for n in CHARACTERS}
    background().save(os.path.join(OUT, "background.png"))
    json.dump({"characters": meta, "mouths": MOUTHS, "eyes": EYES}, open(os.path.join(OUT, "sprites.json"), "w"), indent=1)
    print("built", ", ".join(meta))


def preview(path):
    """Contact sheet of every character with two mouth shapes, for eyeballing."""
    sheet = Image.new("RGB", (len(CHARACTERS) * 300, 640), (60, 34, 40))
    meta = json.load(open(os.path.join(OUT, "sprites.json")))["characters"]
    for i, n in enumerate(CHARACTERS):
        for row, (m, e) in enumerate((("rest", "open"), ("ah", "blink_1"))):
            d = os.path.join(OUT, n); im = Image.open(os.path.join(d, "base.png")).convert("RGBA")
            for sub, key, xy in (("eyes", e, meta[n]["eyes_xy"]), ("mouths", m, meta[n]["mouth_xy"])):
                im.alpha_composite(Image.open(os.path.join(d, sub, f"{key}.png")), tuple(xy))
            im.alpha_composite(Image.open(os.path.join(d, "front.png")), tuple(meta[n]["front"]))
            sheet.paste(im.resize((300, 300), Image.LANCZOS), (i * 300, row * 320), im.resize((300, 300), Image.LANCZOS))
    sheet.save(path)


if __name__ == "__main__":
    main()
    preview(os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview.png"))
