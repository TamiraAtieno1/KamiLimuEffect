import numpy as np, random, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

random.seed(7); np.random.seed(7)
W, H = 1600, 1000
G = "/usr/share/fonts/truetype/google-fonts/"
P = "/usr/share/texmf/fonts/opentype/public/tex-gyre/"
def font(path, size): return ImageFont.truetype(path, size)
LORA_I = G + "Lora-Italic-Variable.ttf"
PAG = P + "texgyrepagella-regular.otf"
PAG_I = P + "texgyrepagella-italic.otf"
INK = (58, 34, 14)

def noise(w, h, scale, octaves=5):
    out = np.zeros((h, w))
    amp = 1.0
    for o in range(octaves):
        s = max(1, int(scale / (2 ** o)))
        small = np.random.rand(h // s + 2, w // s + 2)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((w + s * 2, h + s * 2), Image.BICUBIC)
        out += amp * (np.asarray(im)[:h, :w] / 255.0)
        amp *= 0.5
    out -= out.min(); out /= out.max()
    return out

def parchment(w, h):
    base = np.array([226, 196, 145], float)
    dark = np.array([150, 104, 52], float)
    n = noise(w, h, 260)
    fine = np.random.rand(h, w)
    fibre = noise(w, h, 18, 2)
    t = 0.55 * n + 0.25 * fibre + 0.08 * fine
    t = np.clip((t - 0.35) * 1.4, 0, 1)
    yy, xx = np.mgrid[0:h, 0:w]
    dx = np.minimum(xx, w - xx) / (w * 0.5)
    dy = np.minimum(yy, h - yy) / (h * 0.5)
    edge = np.clip(1 - np.minimum(dx, dy) * 3.2, 0, 1) ** 1.6
    t = np.clip(t * 0.55 + edge * 0.9, 0, 1)
    img = base[None, None, :] * (1 - t[..., None]) + dark[None, None, :] * t[..., None]
    # stains
    for _ in range(4):
        cx, cy, r = random.randint(0, w), random.randint(0, h), random.randint(50, 170)
        ang = np.arctan2(yy - cy, xx - cx)
        wob = 1 + 0.18 * np.sin(3 * ang + random.random() * 6) + 0.1 * np.sin(7 * ang + random.random() * 6)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (r * wob)
        ring = np.exp(-((d - 1) ** 2) / 0.01) * 0.09
        fill = np.clip(1 - d, 0, 1) ** 0.5 * 0.10
        img *= (1 - (ring + fill))[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def ragged_mask(w, h, tear_corner=None):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    pts = []
    for x in range(0, w, 12): pts.append((x, 6 + random.uniform(-5, 5)))
    for y in range(0, h, 12): pts.append((w - 6 + random.uniform(-5, 5), y))
    for x in range(w, 0, -12): pts.append((x, h - 6 + random.uniform(-5, 5)))
    for y in range(h, 0, -12): pts.append((6 + random.uniform(-5, 5), y))
    d.polygon(pts, fill=255)
    if tear_corner == "tl": d.polygon([(0, 0), (70, 0), (52, 18), (30, 34), (14, 58), (0, 75)], fill=0)
    if tear_corner == "br": d.polygon([(w, h), (w - 60, h), (w - 40, h - 22), (w - 20, h - 40), (w, h - 66)], fill=0)
    return m.filter(ImageFilter.GaussianBlur(1))

def page(w, h, tear):
    img = parchment(w, h).convert("RGBA")
    d = ImageDraw.Draw(img)
    # fold creases
    for (a, b) in [((0, h // 2), (w, h // 2 + 6)), ((w // 2, 0), (w // 2 - 4, h))]:
        d.line([a, b], fill=(120, 80, 38, 110), width=3)
        d.line([(a[0] + (1 if a[1] == 0 else 0), a[1] + 3), (b[0] + 1, b[1] + 3)], fill=(245, 225, 185, 90), width=2)
    img.putalpha(ragged_mask(w, h, tear))
    return img

def sketchy_line(d, pts, width=2, jitter=1.5):
    for i in range(2):
        p = [(x + random.uniform(-jitter, jitter), y + random.uniform(-jitter, jitter)) for x, y in pts]
        d.line(p, fill=INK + (200 - i * 80,), width=width - i, joint="curve")

def curve(p0, p1, p2, n=30):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]

def photo_slot(canvas, x, y, w, h, angle, label="add your photo", name="name here"):
    pad, bottom = 14, 50
    card = Image.new("RGBA", (w + pad * 2, h + pad + bottom), (240, 226, 196, 255))
    n = (noise(card.width, card.height, 60, 3) * 25).astype(np.uint8)
    arr = np.asarray(card).copy(); arr[..., :3] = np.clip(arr[..., :3].astype(int) - n[..., None], 0, 255)
    card = Image.fromarray(arr)
    cd = ImageDraw.Draw(card)
    for i in range(0, w, 16):
        cd.line([(pad + i, pad), (pad + min(i + 9, w), pad)], fill=INK + (170,), width=2)
        cd.line([(pad + i, pad + h), (pad + min(i + 9, w), pad + h)], fill=INK + (170,), width=2)
    for j in range(0, h, 16):
        cd.line([(pad, pad + j), (pad, pad + min(j + 9, h))], fill=INK + (170,), width=2)
        cd.line([(pad + w, pad + j), (pad + w, pad + min(j + 9, h))], fill=INK + (170,), width=2)
    f = font(PAG_I, 22)
    tw = cd.textlength("+ " + label, font=f)
    cd.text((pad + (w - tw) / 2, pad + h / 2 - 12), "+ " + label, font=f, fill=INK + (200,))
    if name:
        fn = font("/home/claude/fonts/GreatVibes-Regular.ttf", 30 if w > 180 else 24)
        nw = cd.textlength(name, font=fn)
        cd.text((pad + (w - nw) / 2, pad + h + 4), name, font=fn, fill=(60, 40, 110, 220))
    card = card.rotate(angle, expand=True, resample=Image.BICUBIC)
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    shadow.paste((40, 20, 5, 90), mask=card.split()[3])
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(shadow, (x + 6, y + 8))
    canvas.alpha_composite(card, (x, y))
    # tape
    tape = Image.new("RGBA", (90, 30), (225, 190, 120, 170))
    tape = tape.rotate(angle * 3 + 4, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(tape, (x + card.width // 2 - 45, y - 12))

def banner(d, cx, cy, w, text):
    f = font(LORA_I, 34)
    top = curve((cx - w / 2, cy - 22), (cx, cy - 40), (cx + w / 2, cy - 22))
    bot = curve((cx - w / 2, cy + 26), (cx, cy + 8), (cx + w / 2, cy + 26))
    d.polygon(top + bot[::-1], fill=(236, 214, 170, 255))
    sketchy_line(d, top, 3); sketchy_line(d, bot, 3)
    for s in (-1, 1):
        ex = cx + s * w / 2
        tail = [(ex, cy - 22), (ex + s * 50, cy - 18), (ex + s * 30, cy + 2), (ex + s * 55, cy + 30), (ex, cy + 26)]
        d.polygon(tail, fill=(214, 186, 132, 255))
        sketchy_line(d, tail + [tail[0]], 2)
    tw = d.textlength(text, font=f)
    d.text((cx - tw / 2, cy - 26), text, font=f, fill=INK + (235,))

def acacia(d, x, y, s=1.0):
    sketchy_line(d, [(x, y), (x + 4 * s, y - 60 * s), (x - 2 * s, y - 110 * s)], 4)
    sketchy_line(d, [(x + 2 * s, y - 70 * s), (x + 50 * s, y - 115 * s)], 3)
    sketchy_line(d, [(x, y - 85 * s), (x - 45 * s, y - 118 * s)], 3)
    canopy = curve((x - 110 * s, y - 120 * s), (x, y - 175 * s), (x + 115 * s, y - 120 * s)) + \
             curve((x + 115 * s, y - 120 * s), (x, y - 108 * s), (x - 110 * s, y - 120 * s))
    sketchy_line(d, canopy, 3)
    for i in range(14):
        px = x + random.uniform(-90, 90) * s; py = y - random.uniform(118, 140) * s
        d.line([(px, py), (px + 10 * s, py + 4 * s)], fill=INK + (130,), width=2)

def hills(d, x0, x1, y):
    sketchy_line(d, curve((x0, y), ((x0 + x1) * 0.3, y - 60), ((x0 + x1) / 2, y - 10)), 2)
    sketchy_line(d, curve(((x0 + x1) / 2 - 30, y - 6), (x1 - 80, y - 75), (x1, y + 4)), 2)
    for i in range(10):
        xx = x0 + i * (x1 - x0) / 10
        d.line([(xx, y + 12), (xx + 18, y + 12)], fill=INK + (110,), width=2)

def compass(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK + (200,), width=2)
    d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], outline=INK + (140,), width=1)
    for a in range(0, 360, 45):
        L = r - 4 if a % 90 == 0 else r * 0.6
        rad = math.radians(a)
        tip = (cx + L * math.sin(rad), cy - L * math.cos(rad))
        l = (cx + 8 * math.sin(rad - 1.57), cy - 8 * math.cos(rad - 1.57))
        rr = (cx + 8 * math.sin(rad + 1.57), cy - 8 * math.cos(rad + 1.57))
        d.polygon([tip, l, (cx, cy)], fill=INK + (200,))
        d.polygon([tip, rr, (cx, cy)], outline=INK + (200,))
    d.text((cx - 7, cy - r - 30), "N", font=font(PAG, 22), fill=INK + (220,))

def footpath(d, pts):
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = int(math.hypot(x1 - x0, y1 - y0) / 14)
        for k in range(n):
            if k % 2 == 0:
                t0, t1 = k / n, (k + 1) / n
                d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=INK + (150,), width=2)

def wax_seal(canvas, cx, cy, r, letter):
    s = Image.new("RGBA", (r * 3, r * 3), (0, 0, 0, 0))
    sd = ImageDraw.Draw(s)
    c = r * 1.5
    pts = [(c + (r + random.uniform(-6, 8)) * math.cos(a), c + (r + random.uniform(-6, 8)) * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)]
    sd.polygon(pts, fill=(128, 22, 22, 255))
    sd.ellipse([c - r * 0.72, c - r * 0.72, c + r * 0.72, c + r * 0.72], outline=(80, 10, 10, 255), width=4)
    sd.ellipse([c - r * 0.6, c - r * 0.6, c + r * 0.6, c + r * 0.6], fill=(150, 30, 28, 255))
    f = font(LORA_I, int(r * 0.9))
    tw = sd.textlength(letter, font=f)
    sd.text((c - tw / 2, c - r * 0.6), letter, font=f, fill=(90, 12, 12, 255))
    sd.ellipse([c - r * 0.5, c - r * 0.7, c - r * 0.1, c - r * 0.45], fill=(200, 80, 70, 120))
    shadow = Image.new("RGBA", s.size, (0, 0, 0, 0)); shadow.paste((30, 10, 0, 120), mask=s.split()[3])
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)), (int(cx - c + 4), int(cy - c + 6)))
    canvas.alpha_composite(s, (int(cx - c), int(cy - c)))

if __name__ == '__main__':
    # --- background: dark wood/leather desk
    bg = noise(W, H, 300)
    bgimg = np.stack([40 + bg * 30, 24 + bg * 18, 12 + bg * 8], -1)
    canvas = Image.fromarray(bgimg.astype(np.uint8)).convert("RGBA")
    cd = ImageDraw.Draw(canvas)
    # leather cover behind pages
    cover = Image.new("RGBA", (1460, 900), (0, 0, 0, 0))
    cvd = ImageDraw.Draw(cover)
    cvd.rounded_rectangle([0, 0, 1459, 899], 26, fill=(92, 48, 20, 255))
    cvd.rounded_rectangle([14, 14, 1445, 885], 20, outline=(176, 128, 52, 255), width=3)
    cn = (noise(1460, 900, 40, 3) * 40).astype(int)
    arr = np.asarray(cover).copy(); arr[..., :3] = np.clip(arr[..., :3].astype(int) - cn[..., None], 0, 255)
    cover = Image.fromarray(arr.astype(np.uint8))
    sh = Image.new("RGBA", cover.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 160), mask=cover.split()[3])
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (80, 70))
    canvas.alpha_composite(cover, (70, 50))
    
    PW, PH = 680, 840
    left = page(PW, PH, "tl"); right = page(PW, PH, "br")
    # spine shading on pages
    for img, side in ((left, "r"), (right, "l")):
        a = np.asarray(img).astype(float)
        xx = np.arange(PW)
        dist = (PW - xx) if side == "r" else xx
        sh = np.clip(1 - dist / 90, 0, 1) ** 2 * 0.45
        a[..., :3] *= (1 - sh)[None, :, None]
        img.paste(Image.fromarray(a.astype(np.uint8)))
    
    ld = ImageDraw.Draw(left); rd = ImageDraw.Draw(right)
    
    # LEFT PAGE
    for i, inset in enumerate((40, 52)):
        ld.rectangle([inset, inset, PW - inset, PH - inset], outline=INK + (170 - i * 60,), width=2 - i)
    banner(ld, PW // 2, 120, 380, "Chapter one")
    f = font(PAG_I, 28)
    t = "the first hello"; ld.text((PW / 2 - ld.textlength(t, font=f) / 2, 160), t, font=f, fill=INK + (220,))
    hills(ld, 80, 600, 330)
    acacia(ld, 470, 330, 0.9)
    compass(ld, 150, 270, 46)
    footpath(ld, [(480, 560), (560, 600), (520, 660), (600, 720)])
    
    # RIGHT PAGE
    for i, inset in enumerate((40, 52)):
        rd.rectangle([inset, inset, PW - inset, PH - inset], outline=INK + (170 - i * 60,), width=2 - i)
    fh = font(LORA_I, 30)
    lines = ["To the friends who walked", "this part of the road with me,", "thank you for every late night,", "every laugh, every lesson."]
    for i, L in enumerate(lines):
        rd.text((110, 470 + i * 46), L, font=fh, fill=INK + (225,))
    sketchy_line(rd, curve((110, 665), (300, 650), (480, 672)), 2)
    rd.text((PW / 2 - 18, PH - 100), "~ 2 ~", font=font(PAG_I, 24), fill=INK + (200,))
    
    canvas.alpha_composite(left, (100, 80))
    canvas.alpha_composite(right, (820, 80))
    # spine gutter
    cd = ImageDraw.Draw(canvas)
    for i in range(18):
        cd.line([(800 + i, 85), (800 + i, 915)], fill=(60, 32, 12, 200 - i * 10), width=1)
        cd.line([(818 - i, 85), (818 - i, 915)], fill=(60, 32, 12, 200 - i * 10), width=1)
    
    photo_slot(canvas, 210, 560, 300, 210, -3)
    photo_slot(canvas, 900, 150, 250, 190, 3)
    photo_slot(canvas, 1200, 170, 210, 170, -4)
    wax_seal(canvas, 1380, 820, 48, "T")
    
    # overall vignette
    a = np.asarray(canvas).astype(float)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a[..., :3] *= np.clip(v, 0.55, 1)[..., None]
    Image.fromarray(a.astype(np.uint8)).convert("RGB").save("/home/claude/book_of_tamira_parchment.png")
    print("ok")
