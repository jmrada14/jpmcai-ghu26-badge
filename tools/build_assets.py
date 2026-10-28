"""Build the assets the jpm_payments_ai badge app ships with.

    pip install segno pillow
    python tools/build_assets.py path/to/world.geo.json

world.geo.json is the country outline file from badger/home
(badge/assets/world.geo.json). The outputs are written to the app's assets
folder and committed, so the badge never has to parse the 200KB map itself:

* land.bin      - dots spread evenly over the land, two bytes each
* qr_small.png  - the repo URL as a QR code at 3px a module, for the globe page
* qr_large.png  - the same at 5px a module, for the full screen scan page
* ../icon.png   - the 24x24 menu icon
"""

import json
import math
import os
import sys

import segno
from PIL import Image, ImageDraw

URL = "https://github.com/jpmorgan-payments/ai"

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "badge", "apps", "jpm_payments_ai")
ASSETS = os.path.join(APP, "assets")

# Degrees between rows of dots. Each row is spaced by the same distance along
# the ground, so the dots stay even on the globe instead of bunching at the
# poles.
SPACING = 4.2


def load_rings(path):
    with open(path) as handle:
        countries = json.load(handle)
    rings = []
    for country in countries:
        for polygon in country["polygons"]:
            lons = [p[0] for p in polygon]
            lats = [p[1] for p in polygon]
            rings.append((min(lons), min(lats), max(lons), max(lats), polygon))
    return rings


def on_land(rings, lon, lat):
    for x0, y0, x1, y1, ring in rings:
        if lon < x0 or lon > x1 or lat < y0 or lat > y1:
            continue
        inside = False
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        if inside:
            return True
    return False


def build_land(geojson):
    rings = load_rings(geojson)
    out = bytearray()
    lat = -90 + SPACING / 2
    row = 0
    while lat < 84:
        across = max(1, int(round(360 * math.cos(math.radians(lat)) / SPACING)))
        step = 360 / across
        # stagger alternate rows so the dots sit in a hex-like pattern
        lon = -180 + step * (0.5 if row % 2 else 0.0)
        while lon < 180:
            if lat > -60 and on_land(rings, lon, lat):
                out.append(int(round(lat + 90)))
                out.append(int(round((lon + 180) / 360 * 255)) & 0xFF)
            lon += step
        lat += SPACING
        row += 1
    with open(os.path.join(ASSETS, "land.bin"), "wb") as handle:
        handle.write(out)
    return len(out) // 2


def build_qr(name, scale):
    qr = segno.make(URL, error="m", micro=False)
    path = os.path.join(ASSETS, name)
    # a two module quiet zone; the app frames it in white as well
    qr.save(path, kind="png", scale=scale, border=2, dark="#000000", light="#ffffff")
    return Image.open(path).size, qr.version


def build_icon():
    size = 96
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # a payment card with its stripe and chip, the same design as the menu
    # icon from tools/menu_icon.py
    d.rounded_rectangle((4, 42, 74, 88), radius=8, fill=(10, 22, 52, 255), outline=(80, 200, 255, 255), width=4)
    d.rectangle((6, 52, 72, 60), fill=(80, 200, 255, 255))
    d.rounded_rectangle((13, 67, 29, 78), radius=2, fill=(255, 196, 64, 255))
    # contactless waves off its top corner, in gold
    for r in (14, 25, 36):
        d.arc((54 - r, 38 - r, 54 + r, 38 + r), start=282, end=348, fill=(255, 196, 64, 255), width=7)
    img.resize((24, 24), Image.LANCZOS).save(os.path.join(APP, "icon.png"))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    os.makedirs(ASSETS, exist_ok=True)
    print("land dots:", build_land(sys.argv[1]))
    print("qr_small:", build_qr("qr_small.png", 3))
    print("qr_large:", build_qr("qr_large.png", 5))
    build_icon()
    print("icon: done")


if __name__ == "__main__":
    main()
