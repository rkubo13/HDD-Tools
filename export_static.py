"""Render both pages into self-contained files under dist/.

    python export_static.py

Everything runs in the browser, so the exported files need no Python and no
server. Host dist/ anywhere that serves static files (Cloudflare Pages,
Netlify, GitHub Pages), or open index.html straight off a shared drive.

Re-run this after editing hdd.json.
"""

import base64
import mimetypes
import os

from flask import render_template

from app import IMAGE_DIR, PALLET, WEIGHT_UNIT, app, find_image, get_catalog, image_names

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

STATIC_LINKS = {"home": "index.html", "calculator": "calculator.html"}

PAGES = [("index.html", "lookup"), ("calculator.html", "calculator")]


def inline(name):
    """Artwork goes into the page as a data URI so each file stays standalone."""
    path = os.path.join(IMAGE_DIR, name)
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        raw = f.read()
    return "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii"), len(raw)


def main():
    catalog = get_catalog()
    if not catalog:
        raise SystemExit("No drive data loaded — fix hdd.json before exporting.")

    os.makedirs(OUT_DIR, exist_ok=True)

    images, carried = {}, 0
    for product_id, name in image_names(catalog).items():
        images[product_id], size = inline(name)
        carried += size

    logo_name = find_image("logo")
    logo = None
    if logo_name:
        logo, size = inline(logo_name)
        carried += size

    if carried > 400_000:
        print(f"  note: {carried / 1000:.0f} kB of artwork is baked into every page —"
              " shrink the files in images/ if the pages feel heavy")

    with app.test_request_context():
        for page, page_id in PAGES:
            html = render_template(
                page,
                catalog=catalog,
                weight_unit=WEIGHT_UNIT,
                pallet=PALLET,
                page_id=page_id,
                images=images,
                logo=logo,
                links=STATIC_LINKS,
            )
            with open(os.path.join(OUT_DIR, page), "w", encoding="utf-8") as f:
                f.write(html)

    products = sum(len(g["products"]) for g in catalog)
    print(f"Wrote {', '.join(p for p, _ in PAGES)} to {OUT_DIR} — {products} drives across {len(catalog)} capacities.")


if __name__ == "__main__":
    main()