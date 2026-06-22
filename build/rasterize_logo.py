"""Rasterize the Token logo-mark SVG to a transparent white PNG mask.

Output: assets-src/token-mark.png  (white shape, alpha = coverage)
The face generator tints this to brand green and overlays cracks.
"""
import os
import re
import tempfile

from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SVG_IN = r"C:\Users\User\Desktop\Token marketing HTML\brand-assets\token-logo-mark.svg"
OUT = os.path.join(ROOT, "assets-src", "token-mark.png")

W, H = 400, 492  # render size (matches viewBox aspect 20 : 24.6259)


def main():
    with open(SVG_IN, "r", encoding="utf-8") as f:
        svg = f.read()
    # solid white fill instead of CSS var(); concrete pixel dimensions
    svg = re.sub(r"var\(--fill-0,\s*#?[0-9A-Fa-f]{6}\)", "#FFFFFF", svg)
    svg = svg.replace('width="100%"', f'width="{W}"').replace('height="100%"', f'height="{H}"')

    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as tf:
        tf.write(svg)
        tmp = tf.name
    try:
        drawing = svg2rlg(tmp)
        drawing.width, drawing.height = W, H
        png_tmp = tmp + ".png"
        renderPM.drawToFile(drawing, png_tmp, fmt="PNG", bg=0x000000)
    finally:
        os.unlink(tmp)

    rgb = Image.open(png_tmp).convert("RGB")
    os.unlink(png_tmp)
    # alpha = brightness (white shape on black bg -> opaque shape, transparent bg + hole)
    g = rgb.convert("L")
    out = Image.new("RGBA", rgb.size, (255, 255, 255, 0))
    out.putalpha(g)
    # trim to content bounding box so the mark fills the face frame
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT)
    print(f"Wrote {OUT}  size={out.size}")


if __name__ == "__main__":
    main()
