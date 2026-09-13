"""HDD weight lookup — Flask app.

Reads hdd.json, flattens it into a shape the page can use, and serves:
    GET /                      the weight lookup page
    GET /calculator            the pallet dimensions calculator
    GET /api/drives            the whole catalog as JSON
    GET /api/products/<id>     one product by Product ID
    GET /healthz               liveness check (handy for uptime pings)

The JSON file is the only source of truth. Edit hdd.json and the app picks the
change up on the next request — no restart needed.
"""

import json
import os

from flask import Flask, abort, jsonify, render_template, send_from_directory, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "hdd.json")

# Drop artwork in here and it is picked up by name, no code change needed:
#   images/logo.png                 the mark in the left rail
#   images/PC-HD-SATA6T.jpg         that product's photo on the result card
IMAGE_DIR = os.path.join(BASE_DIR, "images")
IMAGE_EXTS = (".svg", ".png", ".webp", ".avif", ".jpg", ".jpeg")

# The unit the "weight" numbers in hdd.json are recorded in — these are carton
# (box) weights, not bare-drive weights.
WEIGHT_UNIT = "lb"

# Pallet geometry, in inches. A carton is 20 long x 11 wide x 9 high; a layer is
# 2 cartons along the length (40 in) by 4 across the width (44 in), so 8 per
# layer. Change these here and both pages follow.
PALLET = {
    "box": {"length": 20, "width": 11, "height": 9},
    "drives_per_box": 20,
    "boxes_per_layer": 8,
    "cols": 2,   # cartons along the 40 in side
    "rows": 4,   # cartons along the 44 in side
}

app = Flask(__name__)

_cache = {"mtime": None, "catalog": [], "warnings": []}


def _read_raw():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _looks_pro(details):
    if "is_pro" in details:
        return bool(details["is_pro"])
    return "PRO" in str(details.get("item", "")).upper()


def _flatten(group_capacity, blocks, warnings):
    """Turn [{"PC-HD-...": {...}}, ...] into a flat list of product dicts."""
    products = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        for product_id, details in block.items():
            details = details or {}
            listed = details.get("capacity")
            if listed is not None and listed != group_capacity:
                warnings.append(
                    f"{product_id}: listed capacity {listed} TB does not match "
                    f"its group ({group_capacity} TB); using {group_capacity} TB"
                )
            weight = details.get("weight")
            if weight is None:
                warnings.append(f"{product_id}: no weight recorded; skipped")
                continue
            products.append(
                {
                    "product_id": product_id,
                    "item": details.get("item") or f"{group_capacity}TB",
                    "sku": details.get("sku", ""),
                    "capacity": group_capacity,
                    "type": details.get("type"),
                    "is_pro": _looks_pro(details),
                    "weight": weight,
                }
            )
    return products


def build_catalog():
    """Group products by capacity, sorted, with has_multiple derived from the data."""
    warnings = []
    groups = []

    for entry in _read_raw():
        capacity = entry.get("capacity")
        if capacity is None:
            warnings.append("Skipped an entry with no capacity")
            continue

        products = _flatten(capacity, entry.get("products"), warnings)
        if not products:
            warnings.append(f"{capacity} TB has no usable products; skipped")
            continue

        has_multiple = len(products) > 1
        if bool(entry.get("has_multiple")) != has_multiple:
            warnings.append(
                f'{capacity} TB: has_multiple is {str(entry.get("has_multiple")).lower()} '
                f"in the file but it holds {len(products)} product(s)"
            )

        products.sort(key=lambda p: (p["is_pro"], p["item"], p["product_id"]))
        groups.append(
            {
                "capacity": capacity,
                "label": f"{capacity} TB",
                "has_multiple": has_multiple,
                "products": products,
            }
        )

    groups.sort(key=lambda g: g["capacity"])
    return groups, warnings


def get_catalog():
    """Cached catalog, rebuilt whenever hdd.json changes on disk."""
    try:
        mtime = os.path.getmtime(DATA_FILE)
    except OSError:
        app.logger.error("hdd.json not found at %s", DATA_FILE)
        return []

    if _cache["mtime"] != mtime:
        try:
            catalog, warnings = build_catalog()
        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            app.logger.error("hdd.json could not be read: %s", exc)
            return []
        for warning in warnings:
            app.logger.warning("hdd.json: %s", warning)
        _cache.update(mtime=mtime, catalog=catalog, warnings=warnings)

    return _cache["catalog"]


def find_image(stem):
    """First file in images/ named after stem."""
    for ext in IMAGE_EXTS:
        name = stem + ext
        if os.path.exists(os.path.join(IMAGE_DIR, name)):
            return name
    return None


def image_names(catalog):
    """{product_id: filename} for every product that has artwork on disk."""
    found = {}
    for product in all_products(catalog):
        name = find_image(product["product_id"])
        if name:
            found[product["product_id"]] = name
    return found


def all_products(catalog):
    return [p for group in catalog for p in group["products"]]


def page_context(page_id):
    catalog = get_catalog()
    logo = find_image("logo")

    images = {
        product_id: url_for("drive_image", filename=name)
        for product_id, name in image_names(catalog).items()
    }

    return {
        "catalog": catalog,
        "weight_unit": WEIGHT_UNIT,
        "pallet": PALLET,
        "page_id": page_id,
        "images": images,
        "logo": url_for("drive_image", filename=logo) if logo else None,
        "links": {"home": url_for("index"), "calculator": url_for("calculator")},
    }


@app.route("/images/<path:filename>")
def drive_image(filename):
    return send_from_directory(IMAGE_DIR, filename)


@app.route("/")
def index():
    return render_template("index.html", **page_context("lookup"))


@app.route("/calculator")
def calculator():
    return render_template("calculator.html", **page_context("calculator"))


app.add_url_rule("/index.html", "index_html", index)
app.add_url_rule("/calculator.html", "calculator_html", calculator)


@app.errorhandler(404)
def not_found(error):
    home = url_for("index")
    calc = url_for("calculator")
    return (
        "<!DOCTYPE html><html lang=en><meta charset=utf-8>"
        "<title>Page not found</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:12vh auto;max-width:34em;"
        "padding:0 24px;color:#16212b;line-height:1.6}"
        "a{color:#0b4f8a}</style>"
        "<h1>Page not found</h1>"
        "<p>This app has two pages:</p>"
        f'<p><a href="{home}">Hard drive weights</a><br>'
        f'<a href="{calc}">Pallet dimensions calculator</a></p>',
        404,
    )


@app.route("/api/drives")
def api_drives():
    return jsonify({"unit": WEIGHT_UNIT, "pallet": PALLET, "capacities": get_catalog()})


@app.route("/api/products/<product_id>")
def api_product(product_id):
    for product in all_products(get_catalog()):
        if product["product_id"].lower() == product_id.lower():
            return jsonify({"unit": WEIGHT_UNIT, "product": product})
    abort(404, description=f"No product with ID {product_id}")


@app.route("/healthz")
def healthz():
    catalog = get_catalog()
    return jsonify(
        {
            "ok": bool(catalog),
            "capacities": len(catalog),
            "products": len(all_products(catalog)),
        }
    )


if __name__ == "__main__":
    # host="0.0.0.0" so other machines on the office network can reach it too.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)), debug=True)