# The Book of Tamira

A flipbook website for my KamiLimu reflection: *What KamiLimu means to me*.

## Open it

Open `dist/book-of-tamira.html` in Chrome, Edge or Firefox. It's one self-contained file, so it works offline.

- **Turn pages:** use the arrows, the arrow keys, the page corners, or swipe on a phone.
- **Add a photo:** click any photo card (or drag a picture onto it). Click it again to change the photo, or use the × to remove it.
- **Write:** click a name line, a page's text, or a "What this taught me" line and type.
- **Present:** hides the editing hints (shortcut: `P`).
- **Save a copy / Open a copy:** downloads everything you've added as a `.json` file and loads it back. Use this to move your book to another laptop before presenting.

Photos and text are saved in the browser on this computer, so they'll still be there when you reopen the file in the same browser.

## Folder layout

| Path | What it is |
| --- | --- |
| `template.html` | The page: layout, styles and page-turning code |
| `layout.json` | Where every photo card and text block sits on each page |
| `assets/` | The baked artwork: parchment pages, cover, back cover, leather, desk |
| `fonts/` | Lora Italic, Great Vibes, TeX Gyre Pagella Italic (all free licences) |
| `build.py` | Packs everything into `dist/book-of-tamira.html` |
| `art/` | The Python scripts that draw the artwork (`render.py`, `book.py`, `export_assets.py`) |

## Changing things

- Change a page's default text in `layout.json`, then run `python3 build.py`.
- To redraw the artwork (for example to change a chapter title), edit `spreads` in `art/book.py`, then run `python3 art/export_assets.py` followed by `python3 build.py`. The art scripts need Pillow and NumPy, and the font paths at the top of `art/render.py` and `art/book.py` need pointing at the files in `fonts/` (plus the Lora and Pagella .ttf/.otf originals) on your machine.
