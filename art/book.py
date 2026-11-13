import random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from render import (noise, page, sketchy_line, curve, photo_slot, banner, acacia, hills, compass,
                    wax_seal, font, LORA_I, PAG, PAG_I, INK, W, H)

GOLD = (214, 168, 80, 255)

def desk():
    bg = noise(W, H, 300)
    arr = np.stack([40 + bg * 30, 24 + bg * 18, 12 + bg * 8], -1)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

def leather(w, h):
    cover = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(cover)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=(92, 48, 20, 255))
    n = (noise(w, h, 40, 3) * 45).astype(int)
    a = np.asarray(cover).copy(); a[..., :3] = np.clip(a[..., :3].astype(int) - n[..., None], 0, 255)
    return Image.fromarray(a.astype(np.uint8))

def vignette(canvas):
    a = np.asarray(canvas).astype(float)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a[..., :3] *= np.clip(v, 0.55, 1)[..., None]
    return Image.fromarray(a.astype(np.uint8)).convert("RGB")

def shadow_paste(canvas, img, pos, blur=18, alpha=160):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, alpha), mask=img.split()[3])
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)), (pos[0] + 10, pos[1] + 18))
    canvas.alpha_composite(img, pos)

def centered(d, cx, y, text, f, fill):
    d.text((cx - d.textlength(text, font=f) / 2, y), text, font=f, fill=fill)

# ---------- cover

def age_cover(cov, wcx=None):
    rng = np.random.default_rng(5)
    w, h = cov.size
    a = np.asarray(cov).astype(float)
    rgb, al = a[..., :3], a[..., 3]
    yy, xx = np.mgrid[0:h, 0:w]
    # scuffed, lightened edges and corners
    de = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)).astype(float)
    dc = np.minimum.reduce([np.hypot(xx - cx, yy - cy) for cx, cy in ((0, 0), (w, 0), (0, h), (w, h))])
    n1 = noise(w, h, 30, 4)
    edge = np.clip(1 - de / 34, 0, 1) ** 1.5 * (0.5 + n1)
    corner = np.clip(1 - dc / 120, 0, 1) ** 1.2 * (0.6 + n1)
    wear = np.clip(edge + corner, 0, 1)[..., None]
    tan = np.array([150, 98, 54], float)
    rgb = rgb * (1 - wear * 0.6) + tan * wear * 0.6
    wcx = wcx or (w // 2 + 15)
    win = np.zeros((h, w), bool); win[486:806, wcx - 167:wcx + 167] = True
    # patchy faded gold
    gold = ((rgb[..., 0] > 140) & (rgb[..., 0] - rgb[..., 2] > 55))
    fade = (noise(w, h, 22, 3) > 0.6) & gold & ~win
    rgb[fade] = rgb[fade] * 0.62 + np.array([96, 52, 22]) * 0.38
    # crackle in the leather
    cr = noise(w, h, 70, 3)
    cracks = (np.abs(cr - 0.5) < 0.006).astype(float) * 0.22
    cr2 = noise(w, h, 35, 2)
    cracks += (np.abs(cr2 - 0.5) < 0.004).astype(float) * 0.15
    cracks[win] *= 0.3
    rgb *= (1 - cracks[..., None])
    # grime blotches and darker overall tone
    grime = noise(w, h, 160, 3)
    rgb *= (0.78 + 0.22 * grime)[..., None]
    # water ring
    cx, cy, r = w * 0.2, h * 0.5, 95
    d = np.hypot(xx - cx, yy - cy) / r
    rgb *= (1 - (np.exp(-((d - 1) ** 2) / 0.004) * 0.25 + np.clip(1 - d, 0, 1) * 0.06))[..., None]
    a[..., :3] = np.clip(rgb, 0, 255)
    img = Image.fromarray(a.astype(np.uint8))
    d2 = ImageDraw.Draw(img)
    # light scratches
    for _ in range(45):
        x0, y0 = rng.uniform(0, w), rng.uniform(0, h)
        if wcx - 185 < x0 < wcx + 185 and 470 < y0 < 830: continue
        ang, L = rng.uniform(0, math.pi), rng.uniform(15, 90)
        pts = [(x0 + t * L * math.cos(ang) + rng.uniform(-1, 1), y0 + t * L * math.sin(ang) + rng.uniform(-1, 1)) for t in np.linspace(0, 1, 6)]
        d2.line(pts, fill=(176, 126, 80, int(rng.uniform(40, 110))), width=1)
    # chipped, rounded-off corners
    m = Image.new("L", (w, h), 0); md = ImageDraw.Draw(m)
    pts = []
    for x in range(0, w, 6): pts.append((x, rng.uniform(0, 3)))
    for y in range(0, h, 6): pts.append((w - rng.uniform(0, 3), y))
    for x in range(w, 0, -6): pts.append((x, h - rng.uniform(0, 3)))
    for y in range(h, 0, -6): pts.append((rng.uniform(0, 3), y))
    md.polygon(pts, fill=255)
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)):
        k = rng.uniform(14, 26)
        md.polygon([(cx, cy), (cx + sx * k * 1.4, cy), (cx + sx * k * 0.6, cy + sy * k * 0.5), (cx, cy + sy * k * 1.3)], fill=0)
    m = ImageChops.multiply(m, img.split()[3]).filter(ImageFilter.GaussianBlur(0.8))
    img.putalpha(m)
    return img

def render_cover(path):
    random.seed(1); np.random.seed(1)
    c = desk()
    cw, ch = 640, 880
    cov = leather(cw, ch)
    d = ImageDraw.Draw(cov)
    d.rectangle([0, 0, 40, ch], fill=(62, 30, 10, 255))
    for y in (120, 760):
        d.line([(0, y), (40, y)], fill=GOLD, width=3)
    d.rounded_rectangle([70, 40, cw - 40, ch - 40], 14, outline=GOLD, width=3)
    d.rounded_rectangle([84, 54, cw - 54, ch - 54], 10, outline=(176, 128, 52, 255), width=1)
    cx = (70 + cw - 40) // 2
    for (x, y, sx, sy) in [(84, 54, 1, 1), (cw - 54, 54, -1, 1), (84, ch - 54, 1, -1), (cw - 54, ch - 54, -1, -1)]:
        pass
    cover_flowers(cov, cw, ch)
    d = ImageDraw.Draw(cov)
    script_title(cov, d, cx)
    d.line([(cx - 120, 350), (cx + 120, 350)], fill=GOLD, width=2)
    d.polygon([(cx, 340), (cx + 10, 350), (cx, 360), (cx - 10, 350)], fill=GOLD)
    centered(d, cx, 378, "What KamiLimu means to me", font(LORA_I, 30), GOLD)
    # photo window in a gold frame
    px0, py0, px1, py1 = cx - 150, 500, cx + 150, 790
    d.rounded_rectangle([px0 - 14, py0 - 14, px1 + 14, py1 + 14], 10, outline=GOLD, width=3)
    d.rounded_rectangle([px0 - 6, py0 - 6, px1 + 6, py1 + 6], 6, outline=(176, 128, 52, 255), width=1)
    d.rectangle([px0, py0, px1, py1], fill=(236, 216, 176, 255))
    for k in range(px0 + 12, px1 - 12, 16):
        d.line([(k, py0 + 12), (k + 8, py0 + 12)], fill=(120, 80, 38, 255), width=2)
        d.line([(k, py1 - 12), (k + 8, py1 - 12)], fill=(120, 80, 38, 255), width=2)
    for k in range(py0 + 12, py1 - 12, 16):
        d.line([(px0 + 12, k), (px0 + 12, k + 8)], fill=(120, 80, 38, 255), width=2)
        d.line([(px1 - 12, k), (px1 - 12, k + 8)], fill=(120, 80, 38, 255), width=2)
    centered(d, cx, (py0 + py1) // 2 - 16, "+ add your photo", font(PAG_I, 28), (90, 52, 20, 255))
    for (x, y) in ((px0 - 14, py0 - 14), (px1 + 14, py0 - 14), (px0 - 14, py1 + 14), (px1 + 14, py1 + 14)):
        d.polygon([(x, y - 10), (x + 10, y), (x, y + 10), (x - 10, y)], fill=GOLD)
    # worn scuffs
    a = np.asarray(cov).astype(float)
    sc = noise(cw, ch, 120, 4)
    sc[470:820, cx - 175:cx + 175] = 0
    a[..., :3] *= (1 + (sc > 0.78)[..., None] * 0.18)
    cov = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    cov = age_cover(cov)
    shadow_paste(c, cov, ((W - cw) // 2, (H - ch) // 2))
    vignette(c).save(path)

# ---------- ink sketches
def sk_laptop(d, x, y):
    sketchy_line(d, [(x - 110, y - 140), (x + 110, y - 140), (x + 110, y - 10), (x - 110, y - 10), (x - 110, y - 140)], 3)
    sketchy_line(d, [(x - 150, y), (x + 150, y), (x + 120, y - 10), (x - 120, y - 10), (x - 150, y)], 3)
    f = font(PAG, 44)
    centered(d, x, y - 108, "</>", f, INK + (220,))
    for i in range(3):
        d.line([(x - 80, y - 46 + i * 10), (x - 80 + random.randint(60, 150), y - 46 + i * 10)], fill=INK + (120,), width=2)

def sk_fire(d, x, y):
    for a in range(0, 360, 40):
        r = math.radians(a)
        px, py = x + 120 * math.cos(r), y - 60 + 42 * math.sin(r)
        d.ellipse([px - 9, py - 22, px + 9, py - 4], outline=INK + (200,), width=2)
        d.line([(px, py - 4), (px, py + 10)], fill=INK + (200,), width=2)
    sketchy_line(d, [(x - 40, y - 50), (x + 40, y - 70)], 4); sketchy_line(d, [(x - 40, y - 70), (x + 40, y - 50)], 4)
    for s, h in ((-1, 60), (0, 90), (1, 55)):
        fl = curve((x + s * 22 - 18, y - 66), (x + s * 26, y - 66 - h * 1.1), (x + s * 22 + 18, y - 66))
        sketchy_line(d, fl, 2)

def sk_lantern(d, x, y):
    sketchy_line(d, curve((x - 30, y - 200), (x, y - 240), (x + 30, y - 200)), 3)
    sketchy_line(d, [(x - 50, y - 190), (x + 50, y - 190)], 3)
    sketchy_line(d, [(x - 44, y - 190), (x - 50, y - 40), (x + 50, y - 40), (x + 44, y - 190)], 3)
    sketchy_line(d, [(x - 60, y - 40), (x + 60, y - 40), (x + 60, y - 25), (x - 60, y - 25), (x - 60, y - 40)], 3)
    sketchy_line(d, curve((x - 12, y - 80), (x, y - 150), (x + 12, y - 80)) + [(x - 12, y - 80)], 2)
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.line([(x + 80 * math.cos(r), y - 115 + 80 * math.sin(r)), (x + 105 * math.cos(r), y - 115 + 105 * math.sin(r))], fill=INK + (130,), width=2)

def sk_signpost(d, x, y):
    sketchy_line(d, [(x, y), (x, y - 220)], 5)
    for (yy, s, txt) in ((-200, 1, "onward"), (-150, -1, "together"), (-100, 1, "growth")):
        pts = [(x, y + yy - 18), (x + s * 140, y + yy - 18), (x + s * 165, y + yy), (x + s * 140, y + yy + 18), (x, y + yy + 18)]
        sketchy_line(d, pts + [pts[0]], 2)
        f = font(PAG_I, 22)
        tx = x + s * 72
        centered(d, tx, y + yy - 13, txt, f, INK + (210,))
    sketchy_line(d, curve((x - 200, y + 10), (x, y - 10), (x + 200, y + 14)), 2)

def sk_trophy(d, x, y):
    cup = curve((x - 70, y - 210), (x - 70, y - 90), (x, y - 90)) + curve((x, y - 90), (x + 70, y - 90), (x + 70, y - 210))
    sketchy_line(d, cup + [cup[0]], 3)
    sketchy_line(d, curve((x - 70, y - 190), (x - 120, y - 180), (x - 62, y - 130)), 3)
    sketchy_line(d, curve((x + 70, y - 190), (x + 120, y - 180), (x + 62, y - 130)), 3)
    sketchy_line(d, [(x - 10, y - 90), (x - 10, y - 50), (x + 10, y - 50), (x + 10, y - 90)], 3)
    sketchy_line(d, [(x - 55, y - 50), (x + 55, y - 50), (x + 55, y - 20), (x - 55, y - 20), (x - 55, y - 50)], 3)
    for (sx, sy) in ((-150, -200), (150, -170), (-130, -90), (140, -70)):
        px, py = x + sx, y + sy
        d.line([(px - 10, py), (px + 10, py)], fill=INK + (170,), width=2); d.line([(px, py - 10), (px, py + 10)], fill=INK + (170,), width=2)

def sk_quill(d, x, y):
    sketchy_line(d, [(x - 60, y - 20), (x + 60, y - 20), (x + 50, y - 80), (x - 50, y - 80), (x - 60, y - 20)], 3)
    sketchy_line(d, [(x - 30, y - 80), (x - 30, y - 100), (x + 30, y - 100), (x + 30, y - 80)], 3)
    sketchy_line(d, [(x, y - 95), (x + 110, y - 290)], 3)
    fe = curve((x + 20, y - 140), (x + 40, y - 300), (x + 120, y - 300)) + curve((x + 120, y - 300), (x + 110, y - 200), (x + 20, y - 140))
    sketchy_line(d, fe, 2)
    for i in range(8):
        t = 0.2 + i * 0.09
        px, py = x + 110 * t, y - 95 - 195 * t
        d.line([(px, py), (px + 30, py - 4)], fill=INK + (130,), width=2)

def sk_hello(d, x, y):
    hills(d, x - 260, x + 260, y); acacia(d, x + 130, y, 0.9); compass(d, x - 190, y - 60, 46)

def sk_stars(d, x, y):
    for (sx, sy, r) in ((-180, -150, 16), (-60, -200, 10), (80, -160, 20), (190, -210, 12), (0, -90, 14)):
        px, py = x + sx, y + sy
        pts = []
        for k in range(10):
            rr = r if k % 2 == 0 else r * 0.45
            a = math.pi / 2 + k * math.pi / 5
            pts.append((px + rr * math.cos(a), py - rr * math.sin(a)))
        sketchy_line(d, pts + [pts[0]], 2, 0.6)


# ---------- hibiscus ink ornaments (original drawing)
PETAL_FILL = (234, 210, 166, 235)
FLOWER_FILL = (236, 214, 172, 200)
LEAF_FILL = (228, 202, 156, 190)
def _rot(x, y, a):
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

def leaf(d, x, y, length, ang):
    a = math.radians(ang)
    pts_l, pts_r = [], []
    for i in range(0, 41):
        t = i / 40
        w = length * 0.4 * math.sin(math.pi * t ** 0.85) ** 0.9
        serr = 1 + (0.06 if i % 2 else 0) * (t > 0.1)
        pts_l.append(_rot(t * length, -w * serr, a)); pts_r.append(_rot(t * length, w * serr, a))
    poly = [(x + px, y + py) for px, py in pts_l + pts_r[::-1]]
    d.polygon(poly, fill=LEAF_FILL)
    d.line(poly + [poly[0]], fill=INK + (200,), width=2, joint="curve")
    tip = _rot(length, 0, a)
    d.line([(x, y), (x + tip[0] * 0.95, y + tip[1] * 0.95)], fill=INK + (190,), width=2)
    for k in range(1, 5):
        t = k / 5.5
        for sgn in (-1, 1):
            p0 = _rot(t * length, 0, a); p1 = _rot(t * length + length * 0.16, sgn * length * 0.26 * (1 - 0.4 * t), a)
            d.line([(x + p0[0], y + p0[1]), (x + p1[0], y + p1[1])], fill=INK + (140,), width=1)

def hibiscus(d, cx, cy, r, rot):
    rot = math.radians(rot)
    rnd = random.Random(int(cx * 7 + cy * 13))
    order = [0, 2, 4, 1, 3]
    for k in order:
        base = rot + k * 2 * math.pi / 5 + rnd.uniform(-0.08, 0.08)
        rk = r * rnd.uniform(0.88, 1.08)
        width = math.radians(104)
        pts = [(cx, cy)]
        for i in range(61):
            t = i / 60 - 0.5
            ang = base + t * width
            prof = 0.18 + 0.82 * (math.cos(t * math.pi * 0.95) ** 0.35)
            ruff = 0.045 * math.sin(t * 40 + k * 2) + 0.025 * math.sin(t * 77 + k)
            rr = rk * (prof + ruff * (0.3 + abs(t) * 1.6))
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, fill=FLOWER_FILL)
        d.line(pts[1:], fill=INK + (215,), width=3, joint="curve")
        for v in range(-3, 4):
            ang = base + v * width * 0.09
            bend = v * 0.02
            p = [(cx + rk * f * math.cos(ang + bend * f), cy + rk * f * math.sin(ang + bend * f)) for f in (0.14, 0.4, 0.62, 0.78)]
            d.line(p, fill=INK + (95,), width=1)
    for j in range(5):
        ang = rot + j * 2 * math.pi / 5 + math.pi / 5
        d.line([(cx, cy), (cx + r * 0.22 * math.cos(ang), cy + r * 0.22 * math.sin(ang))], fill=INK + (150,), width=1)
    sa = rot + math.radians(25)
    col = curve((cx, cy), (cx + r * 0.8 * math.cos(sa - 0.15), cy + r * 0.8 * math.sin(sa - 0.15)),
                (cx + r * 1.4 * math.cos(sa), cy + r * 1.4 * math.sin(sa)), 20)
    d.line(col, fill=INK + (215,), width=3)
    for j, (px, py) in enumerate(col[11:18]):
        for o in (-1, 1):
            ox, oy = _rot(0, o * 5 * r / 60, sa)
            d.line([(px, py), (px + ox, py + oy)], fill=INK + (170,), width=1)
            d.ellipse([px + ox - 1.5, py + oy - 1.5, px + ox + 1.5, py + oy + 1.5], fill=INK + (200,))
    ex, ey = col[-1]
    for j in range(5):
        a2 = sa + (j - 2) * 0.55
        px, py = ex + r * 0.09 * math.cos(a2), ey + r * 0.09 * math.sin(a2)
        d.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5], outline=INK + (210,), width=1)

def bud(d, x, y, length, ang):
    a = math.radians(ang)
    d.line([(x, y), (x + _rot(length * 0.5, 0, a)[0], y + _rot(length * 0.5, 0, a)[1])], fill=INK + (200,), width=2)
    pts = []
    for i in range(31):
        t = i / 30 * 2 * math.pi
        bx = length * 0.5 + length * 0.35 * (1 - math.cos(t)) * 0.9
        by = length * 0.14 * math.sin(t) * (1 - 0.5 * (1 - math.cos(t)) / 2)
        pts.append(_rot(bx, by, a))
    poly = [(x + px, y + py) for px, py in pts]
    d.polygon(poly, fill=PETAL_FILL); d.line(poly, fill=INK + (215,), width=3)
    for o in (-0.05, 0.05):
        p0 = _rot(length * 0.55, length * o, a); p1 = _rot(length * 1.05, 0, a)
        d.line([(x + p0[0], y + p0[1]), (x + p1[0], y + p1[1])], fill=INK + (130,), width=1)

def corner_cluster(d, x, y, sx, sy, s=1.0):
    def P(dx, dy): return x + sx * dx * s, y + sy * dy * s
    def A(deg):
        a = math.radians(deg)
        return math.degrees(math.atan2(sy * math.sin(a), sx * math.cos(a)))
    leaf(d, *P(10, 30), 120 * s, A(5)); leaf(d, *P(30, 10), 115 * s, A(80))
    leaf(d, *P(90, 60), 85 * s, A(30)); leaf(d, *P(60, 95), 80 * s, A(65))
    bud(d, *P(150, 40), 70 * s, A(-5))
    hibiscus(d, *P(55, 55), 62 * s, A(40))
    hibiscus(d, *P(35, 160), 40 * s, A(75))
    leaf(d, *P(20, 210), 70 * s, A(95))

def side_sprig(d, x, y, vertical, sgn, s=1.0):
    if vertical:
        leaf(d, x, y, 60 * s, 90 + sgn * 20); leaf(d, x, y, 55 * s, -90 - sgn * 20)
        hibiscus(d, x + sgn * 4, y, 26 * s, 90)
    else:
        leaf(d, x, y, 60 * s, 20); leaf(d, x, y, 55 * s, 160)
        hibiscus(d, x, y + sgn * 4, 26 * s, 0)

def decorate_img(img, PW, PH):
    S = 2
    layer = Image.new("RGBA", (PW * S, PH * S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    _decorate(ld, PW * S, PH * S, S)
    layer = layer.resize((PW, PH), Image.LANCZOS)
    img.alpha_composite(layer)

def _decorate(dd, PW, PH, S):
    m = 28 * S
    corner_cluster(dd, m, m, 1, 1, 0.8 * S)
    corner_cluster(dd, PW - m, m, -1, 1, 0.8 * S)
    corner_cluster(dd, m, PH - m, 1, -1, 0.8 * S)
    corner_cluster(dd, PW - m, PH - m, -1, -1, 0.8 * S)
    side_sprig(dd, 34 * S, PH // 2, True, 1, S); side_sprig(dd, PW - 34 * S, PH // 2, True, -1, S)

SCRIPT = "/home/claude/fonts/GreatVibes-Regular.ttf"
def script_title(cov, d, cx):
    f1, f2 = font(SCRIPT, 50), font(SCRIPT, 150)
    centered(d, cx, 104, "The Book of", f1, GOLD)
    tx = cx - d.textlength("Tamira", font=f2) / 2
    ty = 172
    d.text((tx, ty), "Tam\u0131ra", font=f2, fill=(240, 214, 160, 255))
    # find where the dot of the i sits
    m1 = Image.new("L", (600, 260), 0); m2 = Image.new("L", (600, 260), 0)
    ImageDraw.Draw(m1).text((0, 0), "Tami", font=f2, fill=255); ImageDraw.Draw(m2).text((0, 0), "Tam\u0131", font=f2, fill=255)
    diff = np.argwhere(np.asarray(m1).astype(int) - np.asarray(m2).astype(int) > 100)
    dy, dx = diff.mean(axis=0) if len(diff) else (40, 280)
    g = globals()
    saved = (g["INK"], g["FLOWER_FILL"], g["LEAF_FILL"], g["PETAL_FILL"])
    g["INK"] = (232, 192, 108)
    g["FLOWER_FILL"] = (104, 54, 22, 255); g["LEAF_FILL"] = (88, 44, 18, 255); g["PETAL_FILL"] = (104, 54, 22, 255)
    S = 3
    w, h = cov.size
    layer = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    # hibiscus dotting the i
    hibiscus(dd, (tx + dx) * S, (ty + dy - 6) * S, 17 * S, -60)
    # spray on the capital T
    leaf(dd, (tx + 30) * S, (ty + 40) * S, 46 * S, 200); leaf(dd, (tx + 34) * S, (ty + 44) * S, 40 * S, 245)
    hibiscus(dd, (tx + 26) * S, (ty + 40) * S, 28 * S, 210)
    bud(dd, (tx + 44) * S, (ty + 36) * S, 34 * S, -40)
    # trailing sprig off the last a
    ex = tx + d.textlength("Tamira", font=f2)
    leaf(dd, (ex - 8) * S, (ty + 118) * S, 40 * S, 10); leaf(dd, (ex - 8) * S, (ty + 118) * S, 34 * S, 60)
    hibiscus(dd, (ex + 4) * S, (ty + 114) * S, 20 * S, 30)
    cov.alpha_composite(layer.resize((w, h), Image.LANCZOS))
    g["INK"], g["FLOWER_FILL"], g["LEAF_FILL"], g["PETAL_FILL"] = saved

def cover_flowers(cov, cw, ch):
    g = globals()
    saved = (g["INK"], g["FLOWER_FILL"], g["LEAF_FILL"], g["PETAL_FILL"])
    g["INK"] = (222, 178, 92)
    g["FLOWER_FILL"] = (110, 58, 24, 255); g["LEAF_FILL"] = (100, 52, 22, 255); g["PETAL_FILL"] = (110, 58, 24, 255)
    S = 2
    layer = Image.new("RGBA", (cw * S, ch * S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    for (x, y, sx, sy) in [(84, 54, 1, 1), (cw - 54, 54, -1, 1), (84, ch - 54, 1, -1), (cw - 54, ch - 54, -1, -1)]:
        corner_cluster(dd, x * S, y * S, sx, sy, 0.82 * S)
    side_sprig(dd, 96 * S, 480 * S, True, 1, 0.8 * S); side_sprig(dd, (cw - 66) * S, 480 * S, True, -1, 0.8 * S)
    cov.alpha_composite(layer.resize((cw, ch), Image.LANCZOS))
    g["INK"], g["FLOWER_FILL"], g["LEAF_FILL"], g["PETAL_FILL"] = saved

# ---------- spreads
def render_spread(path, cfg, seed):
    random.seed(seed); np.random.seed(seed)
    c = desk()
    shadow_paste(c, leather(1460, 900), (70, 50))
    PW, PH = 680, 840
    left, right = page(PW, PH, "tl" if seed % 2 else None), page(PW, PH, "br")
    for img, side in ((left, "r"), (right, "l")):
        a = np.asarray(img).astype(float)
        xx = np.arange(PW); dist = (PW - xx) if side == "r" else xx
        sh = np.clip(1 - dist / 90, 0, 1) ** 2 * 0.45
        a[..., :3] *= (1 - sh)[None, :, None]
        img.paste(Image.fromarray(a.astype(np.uint8)))
    ld, rd = ImageDraw.Draw(left), ImageDraw.Draw(right)
    for dd in (ld, rd):
        for i, inset in enumerate((40, 52)):
            dd.rectangle([inset, inset, PW - inset, PH - inset], outline=INK + (170 - i * 60,), width=2 - i)
    for img in (left, right):
        decorate_img(img, PW, PH)
    banner(ld, PW // 2, 120, 380, cfg["label"])
    centered(ld, PW / 2, 160, cfg["title"], font(PAG_I, 30), INK + (225,))
    if cfg.get("sketch"):
        cfg["sketch"](ld, PW // 2, cfg.get("sketch_y", 440))
    fh = font(LORA_I, 27)
    if cfg.get("left_text"):
        for i, L in enumerate(cfg["left_text"]):
            ld.text((100, cfg.get("left_text_y", 500) + i * 40), L, font=fh, fill=INK + (225,))
    ty = cfg.get("text_y", 480)
    for i, L in enumerate(cfg.get("text", [])):
        rd.text((100, ty + i * 40), L, font=fh, fill=INK + (225,))
    if cfg.get("lesson", True):
        ly = cfg.get("lesson_y", ty + len(cfg.get("text", [])) * 40 + 30)
        rd.text((100, ly), "What this taught me ~", font=font(PAG_I, 24), fill=(120, 40, 30, 230))
        for k in range(100, 560, 14):
            rd.line([(k, ly + 66), (k + 7, ly + 66)], fill=INK + (130,), width=2)
    centered(rd, PW / 2, PH - 100, f"~ {cfg['page']} ~", font(PAG_I, 24), INK + (200,))
    c.alpha_composite(left, (100, 80)); c.alpha_composite(right, (820, 80))
    cd = ImageDraw.Draw(c)
    for i in range(18):
        cd.line([(800 + i, 85), (800 + i, 915)], fill=(60, 32, 12, 200 - i * 10), width=1)
        cd.line([(818 - i, 85), (818 - i, 915)], fill=(60, 32, 12, 200 - i * 10), width=1)
    for s in cfg["slots"]:
        photo_slot(c, *s)
    if cfg.get("seal", True):
        wax_seal(c, 1380, 820, 46, "T")
    vignette(c).save(path)

LEFT3 = [(150, 300, 250, 185, -3, "photo"), (430, 290, 220, 165, 3, "photo"), (240, 570, 300, 200, 2, "add your photo")]
LEFT4 = [(150, 290, 230, 170, -3, "photo"), (420, 280, 230, 170, 3, "photo"),
         (170, 560, 230, 170, 2, "photo"), (440, 575, 220, 165, -3, "photo")]
R2 = [(900, 150, 250, 190, 3, "add your photo"), (1200, 170, 210, 170, -4, "add your photo")]
spreads = [
    dict(label="Chapter one", title="The first hello", page=2, slots=LEFT3 + R2,
         text=["Where it all began: the nerves,", "the first faces, the first", "sense that I belonged here."]),
    dict(label="Chapter two", title="The path I chose", page=4, slots=LEFT4 + [(960, 150, 330, 230, 2, "add your photo")],
         text=["The Software Engineering track:", "the projects I built, the bugs", "I fought, the skills I grew."]),
    dict(label="Chapter three", title="Around the same fire", page=6, slots=LEFT3 + R2,
         text=["My peer mentorship group,", "the circle where we showed up", "for each other, week after week."]),
    dict(label="Chapter four", title="The hands that held mine", page=8,
         slots=[(150, 300, 200, 160, -3, "mentor", "mentor's name"), (420, 290, 200, 160, 3, "mentor", "mentor's name"),
                (170, 570, 200, 160, 2, "mentor", "mentor's name"), (430, 580, 200, 160, -2, "mentor", "mentor's name"),
                (890, 150, 160, 130, 2, "mentor", "mentor's name"), (1090, 140, 160, 130, -3, "mentor", "mentor's name"), (1290, 155, 140, 130, 2, "mentor", "mentor's name")],
         text=["To my mentors, a note to each:", "Dear ________,", "thank you for ____________."], text_y=420),
    dict(label="Chapter five", title="Fellow travellers", page=10, slots=LEFT4 + R2,
         text=["The peer mentors I had", "the pleasure of meeting,", "and what each one showed me."]),
    dict(label="Chapter six", title="Allies in the arena", page=12,
         slots=LEFT4 + [(880, 140, 160, 130, 3, "photo"), (1075, 130, 160, 130, -2, "photo"), (1270, 145, 150, 130, 3, "photo"),
                (930, 350, 200, 140, -2, "photo"), (1180, 360, 200, 140, 3, "photo")],
         text=["The competitions, and the people", "who turned into friends along the way."], text_y=510, lesson_y=600),
    dict(label="Chapter seven", title="Friends found along the way", page=14, lesson=False,
         slots=[(150, 330, 230, 170, -4, "photo"), (420, 320, 230, 170, 3, "photo"), (180, 580, 230, 170, 2, "photo"),
                (450, 600, 210, 160, -3, "photo"), (880, 140, 240, 180, 3, "photo"), (1170, 150, 240, 180, -3, "photo"),
                (900, 420, 230, 170, -2, "photo"), (1180, 440, 230, 170, 4, "photo")],
         text=["~ the ones who stayed ~"], text_y=680),
    dict(label="Epilogue", title="The girl the pages made", page=16, lesson=False,
         slots=[(150, 300, 230, 190, -3, "me, at the start"), (420, 310, 230, 190, 3, "me, now"),
                (230, 580, 320, 200, 2, "a moment I'm proud of"), (940, 140, 380, 270, -2, "a photo of you now")],
         text=["What KamiLimu means to me:", "the lessons I carry forward,", "and where I am headed next.", "", "~ to be continued ~"], text_y=500),
]

if __name__ == "__main__":
    files = ["00_cover.png"]
    render_cover("00_cover.png")
    for i, cfg in enumerate(spreads, 1):
        fn = f"{i:02d}_{cfg['title'].lower().replace(' ', '_')}.png"
        render_spread(fn, cfg, i + 10); files.append(fn)
    # storyboard
    tw, th = 780, 488
    sheet = Image.new("RGB", (tw * 3 + 80, th * 3 + 80), (30, 18, 8))
    for k, fn in enumerate(files):
        im = Image.open(fn).resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (20 + (k % 3) * (tw + 20), 20 + (k // 3) * (th + 20)))
    sheet.save("book_of_tamira_storyboard.png")
    print(files)
