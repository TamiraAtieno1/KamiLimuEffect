"""Inline the artwork, fonts and layout into one self-contained HTML file."""
import base64, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

def uri(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()

def asset(name):
    p = os.path.join(HERE, "assets", name)
    return uri(p, "image/jpeg" if name.endswith(".jpg") else "image/webp")

html = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
layout = json.load(open(os.path.join(HERE, "layout.json")))

fonts = {"__FONT_LORA__": "lora-italic.woff2", "__FONT_GV__": "greatvibes.woff2", "__FONT_PAG__": "pagella-italic.woff2"}
for k, f in fonts.items():
    html = html.replace(k, uri(os.path.join(HERE, "fonts", f), "font/woff2"))
for name in ("desk.jpg", "leatherL.webp", "leatherR.webp", "cover.webp", "back.webp"):
    html = html.replace(f"__A_{name.split('.')[0]}__", asset(name))

pages = {}
for i in range(1, len(layout["spreads"]) + 1):
    for side in "LR":
        pages[f"p{i}{side}"] = asset(f"p{i}{side}.webp")
html = html.replace("__PAGES__", json.dumps(pages))
html = html.replace("__LAYOUT__", json.dumps(layout))

os.makedirs(os.path.join(HERE, "dist"), exist_ok=True)
out = os.path.join(HERE, "dist", "book-of-tamira.html")
open(out, "w", encoding="utf-8").write(html)
print(out, round(os.path.getsize(out) / 1024), "KB")
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
print("also wrote index.html")