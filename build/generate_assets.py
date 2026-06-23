"""Token DOOM asset generator.

Reads sprites from the user's doom.wad, recolors them to the Token brand
palette, bakes name labels onto monsters and weapons, generates text-box
powerup sprites and a cracked Token-logo player face, and writes everything
into src/ ready to be zipped into a PK3.

Run:  python build/generate_assets.py
"""
import io
import os
import re
import struct
import zlib

from PIL import Image, ImageDraw, ImageFont

import wadlib
import palette as pal

# ---- paths ----------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WAD_PATH = r"D:\Downloads\doom.wad"
SRC = os.path.join(ROOT, "src")
SPRITES = os.path.join(SRC, "sprites")
GRAPHICS = os.path.join(SRC, "graphics")
for d in (SPRITES, GRAPHICS):
    os.makedirs(d, exist_ok=True)

# ---- branding maps --------------------------------------------------------
MONSTERS = {
    "POSS": "NHI",
    "SPOS": "Exposed Secrets",
    "TROO": "AI Agent",
    "SARG": "MCP Server",
    "HEAD": "Shadow AI",
}
WEAPONS = {
    "PUNG": "Finder",
    "PISG": "Secret Scanner",
    "SHTG": "Owner Establisher",
    "CHGG": "Campaign Creator",
    "MISG": "Playbook Launcher",
    "PLSG": "Auto Remediator",
    "BFGG": "Enzo",
}
# Powerup item sprites -> (label, background brand color index)
# (sprite name uses frame A rotation 0 for items)
POWERUPS = {
    "BON1A0": ("Discovery cycle", pal.hex_rgb("#cff851")),   # health bonus
    "BON2A0": ("Ownership point", pal.hex_rgb("#809cff")),   # armor bonus
    "STIMA0": ("Orphan decommissioned", pal.hex_rgb("#06d495")),  # stimpack +10
    "MEDIA0": ("Identity remediated", pal.hex_rgb("#17d079")),    # medikit +25
    "SOULA0": ("Posture restored", pal.hex_rgb("#eecc1d")),  # soulsphere
    "MEGAA0": ("Full coverage", pal.hex_rgb("#cff851")),     # megasphere
    "ARM1A0": ("Least-Privilege plating", pal.hex_rgb("#3cc982")),  # green armor
    "ARM2A0": ("Zero-Trust shielding", pal.hex_rgb("#4c73ff")),    # blue armor
    "CLIPA0": ("Secret-scan clip", pal.hex_rgb("#7367ff")),  # clip
    "AMMOA0": ("Graph queries", pal.hex_rgb("#7367ff")),     # box of bullets
    "CELLA0": ("Remediation charge", pal.hex_rgb("#06d495")),  # cell
    "CELPA0": ("MCP tokens", pal.hex_rgb("#17d079")),        # cell pack (BFG ammo)
    "BPAKA0": ("Coverage backpack", pal.hex_rgb("#3cc982")), # backpack
}

WHITE = (245, 244, 234, 255)   # #f5f4ea (brand off-white)
BLACK = (14, 25, 20, 255)      # #0e1914 (brand near-black)

# ---- fonts ----------------------------------------------------------------
FONT_PATHS = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"]


def load_font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_wh(text, font):
    img = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    return r - l, b - t


# ---- PNG grAb offset chunk ------------------------------------------------
def add_grab(png_bytes, x, y):
    """Insert a ZDoom grAb chunk (sprite offset) right after IHDR."""
    sig = png_bytes[:8]
    ihdr_end = 8 + 25  # sig + (len4 + 'IHDR'4 + data13 + crc4)
    data = struct.pack(">ii", x, y)
    chunk = struct.pack(">I", 8) + b"grAb" + data
    chunk += struct.pack(">I", zlib.crc32(b"grAb" + data) & 0xffffffff)
    return sig + png_bytes[8:ihdr_end] + chunk + png_bytes[ihdr_end:]


def save_sprite(img, name, folder, xoff, yoff):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    out = add_grab(buf.getvalue(), xoff, yoff)
    with open(os.path.join(folder, name + ".png"), "wb") as f:
        f.write(out)


# ---- label baking ---------------------------------------------------------
def bake_label(img, leftoff, topoff, text, bar_h=11, font_size=10):
    """Add a white bar with black text under the sprite. Widen canvas if the
    text is wider than the sprite, keeping the body centered (offset adjusted)."""
    w, h = img.size
    font = load_font(font_size)
    tw, th = text_wh(text, font)
    new_w = max(w, tw + 4)
    pad = (new_w - w) // 2
    canvas = Image.new("RGBA", (new_w, h + bar_h), (0, 0, 0, 0))
    canvas.paste(img, (pad, 0))
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, h, new_w - 1, h + bar_h - 1], fill=WHITE)
    d.text(((new_w - tw) // 2, h + (bar_h - th) // 2 - 1), text, fill=BLACK, font=font)
    return canvas, leftoff + pad, topoff


# ---- builders -------------------------------------------------------------
def build_palette(wad):
    raw = wadlib.read_playpal_raw(wad)
    out = pal.remap_playpal_lump(raw)
    with open(os.path.join(SRC, "PLAYPAL.lmp"), "wb") as f:
        f.write(out)
    print(f"  PLAYPAL remapped ({len(out)} bytes)")


def build_labeled(wad, rmap, prefixes, folder, big):
    n = 0
    for prefix, label in prefixes.items():
        frames = wad.names_with_prefix(prefix)
        for name in frames:
            raw = wad.read(name)
            img, lo, to = wadlib.decode_picture(raw, rmap)
            bar_h, fs = (14, 13) if big else (11, 10)
            img, lo, to = bake_label(img, lo, to, label, bar_h=bar_h, font_size=fs)
            save_sprite(img, name, folder, lo, to)
            n += 1
    return n


def build_powerups():
    n = 0
    for name, (label, bg) in POWERUPS.items():
        font = load_font(10)
        tw, th = text_wh(label, font)
        w, h = tw + 8, th + 8
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], fill=bg + (255,))
        d.rectangle([0, 0, w - 1, h - 1], outline=WHITE, width=1)
        d.text((4, 3), label, fill=BLACK, font=font)
        # item offset: centered horizontally, origin at bottom (sits on floor)
        save_sprite(img, name, SPRITES, w // 2, h)
        n += 1
    return n


def make_logo_face(size, cracks):
    """Placeholder Token-logo face. `cracks` 0..5 = damage level."""
    img = Image.new("RGBA", (size, size), pal.hex_rgb("#00352a") + (255,))
    d = ImageDraw.Draw(img)
    m = 3
    # "token" = a rounded shield/coin
    d.ellipse([m, m, size - m, size - m], fill=pal.hex_rgb("#17d079") + (255,),
              outline=pal.hex_rgb("#f5f4ea") + (255,), width=2)
    d.text((size // 2 - 6, size // 2 - 6), "T", fill=BLACK, font=load_font(size - 12))
    # cracks scale with damage
    crack_lines = [
        [(size // 2, m), (size // 2 + 3, size // 2)],
        [(size // 2 + 3, size // 2), (size - m, size // 2 + 4)],
        [(m, size // 2 + 2), (size // 2, size // 2 + 5)],
        [(size // 2, size // 2 + 5), (size // 2 - 4, size - m)],
        [(size // 2 + 2, size // 2), (size // 2 + 8, size - m)],
    ]
    for i in range(min(cracks, len(crack_lines))):
        d.line(crack_lines[i], fill=pal.hex_rgb("#f3bfbf") + (255,), width=1)
    return img


def build_faces(wad):
    """Replace every STF* face lump with a cracked-logo frame keyed to its
    pain tier (the digit in the name: 0 = healthy ... 4 = near death)."""
    n = 0
    faces = [nm for nm in wad.names_with_prefix("STF") if nm not in ("STFB1", "STFB0")]
    for name in set(faces):
        raw = wad.read(name)
        # original size, for matching offsets
        try:
            w, h, lo, to = struct.unpack("<hhhh", raw[:8])
        except struct.error:
            continue
        if w <= 0 or h <= 0 or w > 64 or h > 64:
            continue
        if name.startswith("STFDEAD"):
            tier = 5
        elif name.startswith("STFGOD"):
            tier = 0
        else:
            m = re.search(r"(\d)", name)
            tier = int(m.group(1)) if m else 0
        face = make_logo_face(max(w, h), tier)
        face = face.resize((w, h))
        save_sprite(face, name, GRAPHICS, lo, to)
        n += 1
    return n


def main():
    print("Loading WAD:", WAD_PATH)
    wad = wadlib.WAD(WAD_PATH)
    rmap = pal.remap_base(wadlib.base_palette(wad))

    print("Palette:")
    build_palette(wad)

    print("Monsters:")
    mn = build_labeled(wad, rmap, MONSTERS, SPRITES, big=False)
    print(f"  {mn} monster frames")

    print("Weapons:")
    wn = build_labeled(wad, rmap, WEAPONS, SPRITES, big=True)
    print(f"  {wn} weapon frames")

    print("Powerups:")
    pn = build_powerups()
    print(f"  {pn} powerup sprites")

    print("Faces:")
    fn = build_faces(wad)
    print(f"  {fn} face frames")

    print("Done.")


if __name__ == "__main__":
    main()
