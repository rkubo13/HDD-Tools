# Hard drive weights + pallet calculator

Two pages:

- **Hard Drive Searcher** — pick a capacity, get the carton weight. Capacities
  that stock more than one drive open a list of their options on hover (tap on a
  touchscreen). Shows Product ID, SKU, capacity and weight, each copyable. Drives
  can be selected several at a time: the first pick of a visit searches on its
  own, further picks gather in the Selected list and go on Send, and results come
  back in the order they were chosen. The chip ringed with moving dashes is the
  one the next pick overwrites — press + to start a new chip instead, or click any
  chip to aim at that one.
- **Pallet dimensions calculator** — enter each product and how many units were
  ordered, get pallet length × width × height in inches and total weight in lbs,
  plus a "Copy Dimensions & Weight" button that puts both on the clipboard as
  dot-leader lines ready to paste into Google Chat.

```
hdd-lookup/
├── app.py                   Flask app + JSON API
├── hdd.json                 the only place drive data lives
├── templates/
│   ├── _base.html           shell, theme, and the product picker component
│   ├── index.html           weight lookup
│   └── calculator.html      pallet calculator
├── images/                  artwork, picked up by filename
├── export_static.py         bakes both pages into dist/
└── requirements.txt
```

## Artwork

Drop files into `images/` and they appear — no code change:

- `logo.png` (or .svg, .webp, .avif, .jpg) becomes the mark in the left rail.
- `PC-HD-SATA6T.jpg` becomes that product's photo on its result card. The name
  must match the Product ID in `hdd.json` exactly.

Anything without a file falls back to drawn artwork, so the layout holds either
way. Flask serves `images/` directly and picks up new files on reload; the static
export base64-inlines them so each page stays a standalone file, which is why it
is worth keeping them small — the export warns past about 400 kB total.

Both pages open with colour gathered behind the title that drains away down the
page — a radial glow over a vertical wash, both in `.workspace` in
`templates/_base.html`. The title, subtitle and input rise into place on load,
staggered, and hold still for anyone with reduced motion turned on.

## Theme

Every style for both pages lives in one `<style>` block at the top of
`templates/_base.html`, with the palette as CSS variables — `--brand` drives the
rail and every primary control. The layout is a fixed left rail plus a workspace
column; under 940px the rail folds into a top bar.

Both pages share one input shape, the composer bubble, centred under the page
title. On the lookup page the search field and its list are a single bubble that
unfolds when you click into it, with the Selected list along its bottom edge; on
the calculator the bubble holds the product rows. Either way, add sits on the
left and clear and send on the right. Sub-lists for capacities with several
models stay separate floating bubbles.

## How the pallet math works

Cartons are 20 × 11 × 9 in (L × W × H) and hold 20 drives each. A layer is 2
cartons along the length and 4 across the width — 40 × 44 in, 8 cartons. Extra
cartons start a new layer and add 9 in of height.

    cartons per product = drives ordered / 20
    layers              = ceil(total cartons / 8)
    height              = layers × 9
    footprint           = 40 × 44 once there are 8 or more cartons

Quantities must be multiples of 20 (full cases only). A part-filled carton has no defined weight
(the data holds carton weights only), so the calculator rejects the row and says
which nearby quantities work rather than rounding up and reporting a weight that
is wrong.

Under 8 cartons there is no full layer, and the footprint follows the order the
cartons actually go down in. Pairs sit long-side to long-side; a leftover odd
carton turns 90° and lies across the seam between the two columns, so it claims
a whole 11 in row rather than half of one.

    cartons   bottom layer                          footprint
    1         1 carton                              20 × 11 × 9
    2         2, long sides together                20 × 22 × 9
    3         2 plus 1 turned crosswise beside them 31 × 22 × 9
    4         2 × 2                                 40 × 22 × 9
    5         2 × 2 plus 1 across the middle        40 × 33 × 9
    6         2 × 3                                 40 × 33 × 9
    7         2 × 3 plus 1 across the middle        40 × 44 × 9
    8         2 × 4, full layer                     40 × 44 × 9

Weight excludes the pallet, wrap and slip sheets. All of the geometry lives in
`PALLET` in `app.py` — change it there and both pages follow.

The logistics message pads each label out to a fixed character column
(`LEADER_COLUMN` in `templates/calculator.html`) with dots, two spaces apart, so
the two values start at the same character:

    Pallet Dimensions (L x W x H) .  .  .  .  .  .  40 x 44 x 27 in
    Total Weight .  .  .  .  .  .  .  .  .  .  .    662.5 lbs

Chat clients using a proportional font will line these up closely but not
perfectly, since a dot and a space are not the same width. Wrapping the paste in
backticks forces a monospace font and makes it exact.

## The pallet view

The result draws the load next to the breakdown table: drag to turn it, double
click to reset the angle. It is hand-rolled SVG — every carton and pallet board
is an axis-aligned box, so each projects to at most three visible faces, which
get sorted back to front and drawn as polygons. No Three.js, no CDN, nothing to
load at runtime, so the exported file still works with no internet.

Full layers are drawn as a solid 2 × 4 block. Any leftover cartons sit on top in
the arrangement from the table above, centred on the pallet. The pallet itself is
drawn 5.5 in tall and is not counted in the quoted height.

Every carton carries two labels — manufacturer barcodes on the left, shipping
label on the right. They go on the carton's end face, the one at right angles to
its 20 in length, on whichever side points away from the middle of the pallet, so
a 2 × 4 layer has the left column labelled left and the right column labelled
right, and a carton turned across the layer is labelled on its own outward end.
Both are drawn once into `<defs>` and stamped onto a face with an affine
transform, so turning the pallet costs one `<use>` per label rather than
re-drawing every bar. A label that lands under 15 units wide on screen — roughly
eight layers and up — swaps to a plain stand-in, and under 3.5 it is skipped, so
a tall pallet does not pay for barcodes nobody can see.

## Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000. Other machines on the office network can reach
it at `http://<your-ip>:5000` while it's running.

## Adding or changing drives

Edit `hdd.json` only. The app re-reads the file whenever it changes, so no
restart is needed. The shape is:

```json
{
  "capacity": 8,
  "products": [
    { "PC-HD-SATA8T-PRO": { "item": "8TB PRO", "sku": "DHWD8002PURP", "capacity": 8, "weight": 33.25 } }
  ]
}
```

Whether a capacity opens a submenu is decided by how many products it holds, not
by the `has_multiple` flag — one less field to keep in sync. The flag is still
read and mismatches are logged as warnings so the file can be cleaned up.

Two things in the current data are worth fixing at the source:

- `PC-HD-SATA3T-33PURZ` (3 TB group) lists `"capacity": 4`. The app uses the
  group's capacity, 3 TB.
- `has_multiple` disagrees with the product count on 3, 10, 12, 14, 18 and 26 TB.

Weights are carton weights in pounds, labelled `lb` via `WEIGHT_UNIT` at the top
of `app.py`.

## API

| Route | Returns |
| --- | --- |
| `/api/drives` | every capacity and product, plus the pallet constants |
| `/api/products/<product_id>` | one product, 404 if unknown |
| `/healthz` | `{"ok": true, "capacities": 11, "products": 13}` |

## Deploying for free

### Option A — static hosting (recommended: free, instant, never sleeps)

All the lookup logic runs in the browser, so the page doesn't need Python once
the data is baked in:

```bash
python export_static.py     # writes dist/index.html and dist/calculator.html
```

Upload that folder to any static host:

- **Cloudflare Pages** — create a project, drag the `dist` folder into the
  direct-upload box. Free, unlimited, no cold starts.
- **Netlify Drop** — drag `dist` onto app.netlify.com/drop.
- **GitHub Pages** — push the contents of `dist` to a `gh-pages` branch and
  enable Pages in the repo settings.

Re-run `export_static.py` and re-upload after editing `hdd.json`.

### Option B — Render free web service (keeps Flask and the API)

Push the folder to GitHub, then on Render: New → Web Service → connect the repo.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Instance type: Free

Free web services sleep after 15 minutes without traffic and take roughly a
minute to wake on the next request, so the first lookup each morning is slow.
Everything after that is fast.

### Option C — run it on the office PC

Install Python, then serve it with a production server instead of the Flask dev
server:

```bash
pip install waitress
waitress-serve --port=8000 app:app
```

Add it to Task Scheduler with "run at startup" and the warehouse can bookmark
`http://<that-pc-name>:8000`. Nothing leaves the building and nothing sleeps.
