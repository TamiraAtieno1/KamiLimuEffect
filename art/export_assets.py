"""Bake the static artwork of The Book of Tamira into web images + a JSON layout file."""
import json, os, random, math
import numpy as np
from PIL import Image, ImageDraw
import book
from book import (leather, age_cover, cover_flowers, script_title, centered, decorate_img, banner,
                  wax_seal, page, noise, spreads, GOLD, font, LORA_I, PAG_I, INK)

OUT = "/home/claude/flipbook/assets"
os.makedirs(OUT, exist_ok=True)
PW, PH = 680, 840
FACE_W, FACE_H = 730, 900

def save(img, name, q=80):
    img.save(os.path.join(OUT, name), "WEBP", quality=q, method=6)

def shade(img, side):
    a = np.asarray(img).astype(float)
    xx = np.arange(PW); dist = (PW - xx) if side == "r" else xx
    sh = np.clip(1 - dist / 90, 0, 1) ** 2 * 0.45
    a[..., :3] *= (1 - sh)[None, :, None]
    img.paste(Image.fromarray(a.astype(np.uint8)))

def bake_spread(i, cfg):
    seed = i + 10
    random.seed(seed); np.random.seed(seed)
    _ = leather(1460, 900)  # keep the random stream identical to the preview pictures
    left, right = page(PW, PH, "tl" if seed % 2 else None), page(PW, PH, "br")
    shade(left, "r"); shade(right, "l")
    ld, rd = ImageDraw.Draw(left), ImageDraw.Draw(right)
    for dd in (ld, rd):
        for k, inset in enumerate((40, 52)):
            dd.rectangle([inset, inset, PW - inset, PH - inset], outline=INK + (170 - k * 60,), width=2 - k)
    for img in (left, right):
        decorate_img(img, PW, PH)
    banner(ld, PW // 2, 120, 380, cfg["label"])
    centered(ld, PW / 2, 160, cfg["title"], font(PAG_I, 30), INK + (225,))
    if cfg.get("lesson", True):
        ty = cfg.get("text_y", 480)
        ly = cfg.get("lesson_y", ty + len(cfg.get("text", [])) * 40 + 30)
        rd.text((100, ly), "What this taught me ~", font=font(PAG_I, 24), fill=(120, 40, 30, 230))
    centered(rd, PW / 2, PH - 100, f"~ {cfg['page']} ~", font(PAG_I, 24), INK + (200,))
    # wax seal (canvas 1380,820 -> right page 560,740)
    big = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    wax_seal(big, 560, 740, 46, "T")
    right.alpha_composite(big)
    save(left, f"p{i}L.webp"); save(right, f"p{i}R.webp")

def bake_cover():
    random.seed(1); np.random.seed(1)
    cw, ch = FACE_W, FACE_H
    cov = leather(cw, ch)
    d = ImageDraw.Draw(cov)
    d.rectangle([0, 0, 40, ch], fill=(62, 30, 10, 255))
    for y in (120, ch - 120):
        d.line([(0, y), (40, y)], fill=GOLD, width=3)
    d.rounded_rectangle([70, 40, cw - 40, ch - 40], 14, outline=GOLD, width=3)
    d.rounded_rectangle([84, 54, cw - 54, ch - 54], 10, outline=(176, 128, 52, 255), width=1)
    cx = (70 + cw - 40) // 2
    cover_flowers(cov, cw, ch)
    d = ImageDraw.Draw(cov)
    script_title(cov, d, cx)
    d.line([(cx - 120, 350), (cx + 120, 350)], fill=GOLD, width=2)
    d.polygon([(cx, 340), (cx + 10, 350), (cx, 360), (cx - 10, 350)], fill=GOLD)
    centered(d, cx, 378, "What KamiLimu means to me", font(LORA_I, 30), GOLD)
    px0, py0, px1, py1 = cx - 150, 500, cx + 150, 790
    d.rounded_rectangle([px0 - 14, py0 - 14, px1 + 14, py1 + 14], 10, outline=GOLD, width=3)
    d.rounded_rectangle([px0 - 6, py0 - 6, px1 + 6, py1 + 6], 6, outline=(176, 128, 52, 255), width=1)
    d.rectangle([px0, py0, px1, py1], fill=(236, 216, 176, 255))
    for (x, y) in ((px0 - 14, py0 - 14), (px1 + 14, py0 - 14), (px0 - 14, py1 + 14), (px1 + 14, py1 + 14)):
        d.polygon([(x, y - 10), (x + 10, y), (x, y + 10), (x - 10, y)], fill=GOLD)
    a = np.asarray(cov).astype(float)
    sc = noise(cw, ch, 120, 4)
    sc[470:820, cx - 175:cx + 175] = 0
    a[..., :3] *= (1 + (sc > 0.78)[..., None] * 0.18)
    cov = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    cov = age_cover(cov, cx)
    save(cov, "cover.webp", 84)
    return dict(x=px0, y=py0, w=px1 - px0, h=py1 - py0)

def bake_back():
    random.seed(3); np.random.seed(3)
    cw, ch = FACE_W, FACE_H
    cov = leather(cw, ch)
    d = ImageDraw.Draw(cov)
    d.rectangle([cw - 40, 0, cw, ch], fill=(62, 30, 10, 255))
    for y in (120, ch - 120):
        d.line([(cw - 40, y), (cw, y)], fill=GOLD, width=3)
    d.rounded_rectangle([40, 40, cw - 70, ch - 40], 14, outline=GOLD, width=3)
    d.rounded_rectangle([54, 54, cw - 84, ch - 54], 10, outline=(176, 128, 52, 255), width=1)
    cover_flowers_back(cov, cw, ch)
    d = ImageDraw.Draw(cov)
    cx = (40 + cw - 70) // 2
    centered(d, cx, 410, "~ to be continued ~", font(book.SCRIPT, 48), GOLD)
    cov = age_cover(cov, cx)
    save(cov.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_LEFT_RIGHT), "back.webp", 84)

def cover_flowers_back(cov, cw, ch):
    g = book.__dict__
    saved = (g["INK"], g["FLOWER_FILL"], g["LEAF_FILL"], g["PETAL_FILL"])
    g["INK"] = (222, 178, 92)
    g["FLOWER_FILL"] = (104, 54, 22, 255); g["LEAF_FILL"] = (88, 44, 18, 255); g["PETAL_FILL"] = (104, 54, 22, 255)
    S = 2
    layer = Image.new("RGBA", (cw * S, ch * S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    for (x, y, sx, sy) in [(54, 54, 1, 1), (cw - 84, 54, -1, 1), (54, ch - 54, 1, -1), (cw - 84, ch - 54, -1, -1)]:
        book.corner_cluster(dd, x * S, y * S, sx, sy, 0.82 * S)
    cov.alpha_composite(layer.resize((cw, ch), Image.LANCZOS))
    g["INK"], g["FLOWER_FILL"], g["LEAF_FILL"], g["PETAL_FILL"] = saved

def bake_leather():
    random.seed(42); np.random.seed(42)
    lt = leather(1460, 900)
    a = np.asarray(lt).astype(float)
    xx = np.arange(1460)
    spine = np.clip(1 - np.abs(xx - 730) / 40, 0, 1) ** 1.5 * 0.55
    a[..., :3] *= (1 - spine)[None, :, None]
    lt = Image.fromarray(a.astype(np.uint8))
    save(lt.crop((0, 0, 730, 900)), "leatherL.webp", 78)
    save(lt.crop((730, 0, 1460, 900)), "leatherR.webp", 78)

def bake_desk():
    random.seed(9); np.random.seed(9)
    n = noise(512, 512, 200)
    n2 = noise(512, 512, 30, 3)
    t = 0.75 * n + 0.25 * n2
    arr = np.stack([40 + t * 30, 24 + t * 18, 12 + t * 8], -1)
    Image.fromarray(arr.astype(np.uint8)).save(os.path.join(OUT, "desk.jpg"), quality=78)

def card_layout(slot, side):
    x, y, w, h, angle, label = slot[:6]
    name = slot[6] if len(slot) > 6 else "name here"
    cw_, ch_ = w + 28, h + 14 + 50
    rad = math.radians(angle)
    bw = abs(cw_ * math.cos(rad)) + abs(ch_ * math.sin(rad))
    bh = abs(cw_ * math.sin(rad)) + abs(ch_ * math.cos(rad))
    ox, oy = (100, 80) if side == "L" else (820, 80)
    ccx, ccy = x - ox + bw / 2, y - oy + bh / 2
    return dict(left=round(ccx - cw_ / 2, 1), top=round(ccy - ch_ / 2, 1), w=w, h=h, rot=-angle,
                label=label, name=name)

if __name__ == "__main__":
    layout = {"spreads": []}
    for i, cfg in enumerate(spreads, 1):
        bake_spread(i, cfg)
        cards = {"L": [], "R": []}
        for s in cfg["slots"]:
            side = "L" if s[0] < 800 else "R"
            cards[side].append(card_layout(s, side))
        ty = cfg.get("text_y", 480)
        entry = dict(label=cfg["label"], title=cfg["title"], cards=cards,
                     text=cfg.get("text", []), text_y=ty, lesson=cfg.get("lesson", True))
        if entry["lesson"]:
            entry["lesson_y"] = cfg.get("lesson_y", ty + len(cfg.get("text", [])) * 40 + 30)
        layout["spreads"].append(entry)
        print("spread", i)
    layout["coverWindow"] = bake_cover()
    bake_back(); bake_leather(); bake_desk()
    json.dump(layout, open("/home/claude/flipbook/layout.json", "w"), indent=1)
    print(sorted(os.listdir(OUT)))
