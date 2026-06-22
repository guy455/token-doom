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
    "SARG": "MCP Server",         # also the Spectre
    "HEAD": "Shadow AI",
    "SKUL": "Rogue Token",        # Lost Soul
    "BOSS": "Privilege Escalation",  # Baron of Hell (E1M8 boss)
    "CYBR": "Nation-State APT",    # Cyberdemon
    "SPID": "Rogue Superintelligence",  # Spider Mastermind
}
# Held weapon view sprites (name overlaid on the gun).
WEAPONS = {
    "PUNG": "Finder",
    "PISG": "Secret Scanner",
    "SHTG": "Owner Establisher",
    "CHGG": "Campaign Creator",
    "MISG": "Playbook Launcher",
    "PLSG": "Auto Remediator",
    "BFGG": "Enzo",
}
# Ground pickup sprites for weapons (name labeled below, like monsters).
WEAPON_PICKUPS = {
    "SHOT": "Owner Establisher",
    "MGUN": "Campaign Creator",
    "LAUN": "Playbook Launcher",
    "PLAS": "Auto Remediator",
    "BFUG": "Enzo",
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


def overlay_label(img, text, font_size=12):
    """Draw the name bar ONTO the sprite near the bottom of its content,
    without changing canvas size (so the sprite offsets stay valid)."""
    w, h = img.size
    font = load_font(font_size)
    tw, th = text_wh(text, font)
    fs = font_size
    while tw > w - 2 and fs > 6:
        fs -= 1
        font = load_font(fs)
        tw, th = text_wh(text, font)
    bar_h = th + 3
    bbox = img.getbbox() or (0, 0, w, h)
    # anchor near the TOP of the gun so the name stays above the status bar
    bar_top = max(0, bbox[1] + 2)
    bar_bottom = min(h, bar_top + bar_h)
    bx0 = max(0, (w - (tw + 4)) // 2)
    bx1 = min(w, bx0 + tw + 4)
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([bx0, bar_top, bx1 - 1, bar_bottom - 1], fill=WHITE)
    d.text((bx0 + 2, bar_top + 1), text, fill=BLACK, font=font)
    return out


# ---- builders -------------------------------------------------------------
def build_palette(wad):
    raw = wadlib.read_playpal_raw(wad)
    out = pal.remap_playpal_lump(raw)
    with open(os.path.join(SRC, "PLAYPAL.lmp"), "wb") as f:
        f.write(out)
    print(f"  PLAYPAL remapped ({len(out)} bytes)")


def build_labeled(wad, rmap, prefixes, folder, big=False, mode="below"):
    n = 0
    for prefix, label in prefixes.items():
        for name in wad.names_with_prefix(prefix):
            raw = wad.read(name)
            img, lo, to = wadlib.decode_picture(raw, rmap)
            if mode == "overlay":
                img = overlay_label(img, label, font_size=12)
            else:
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


_MARK = None


def get_mark():
    global _MARK
    if _MARK is None:
        _MARK = Image.open(os.path.join(ROOT, "assets-src", "token-mark.png")).convert("RGBA")
    return _MARK


def tint_mask(mask_img, rgb):
    """Recolor an RGBA image to a flat color, keeping its alpha."""
    solid = Image.new("RGBA", mask_img.size, rgb + (255,))
    solid.putalpha(mask_img.split()[3])
    return solid


# bold jagged cracks as fraction-of-face polylines (drawn from tier 1 up)
_CRACKS = [
    [(0.50, 0.03), (0.45, 0.24), (0.55, 0.40)],
    [(0.55, 0.40), (0.80, 0.30), (0.97, 0.42)],
    [(0.45, 0.24), (0.18, 0.16), (0.03, 0.28)],
    [(0.55, 0.40), (0.49, 0.70), (0.40, 0.98)],
    [(0.55, 0.40), (0.72, 0.68), (0.78, 0.98)],
]

# face palette
_GREEN = pal.hex_rgb("#17d079")
_LIME = pal.hex_rgb("#cff851")
_CREAM = pal.hex_rgb("#f5f4ea")
_INK = pal.hex_rgb("#0e1914")
_PINK = pal.hex_rgb("#f3bfbf")
_BLUE = pal.hex_rgb("#809cff")
_BG = pal.hex_rgb("#03251e")


def _brows(d, mode, by=16, ex1=48, ex2=80):
    w, ink = 6, _INK + (255,)
    if mode == "angry":
        d.line([ex1 - 15, by - 7, ex1 + 13, by + 5], fill=ink, width=w)
        d.line([ex2 - 13, by + 5, ex2 + 15, by - 7], fill=ink, width=w)
    elif mode == "sad":
        d.line([ex1 - 13, by + 6, ex1 + 15, by - 6], fill=ink, width=w)
        d.line([ex2 - 15, by - 6, ex2 + 13, by + 6], fill=ink, width=w)
    elif mode == "happy":
        d.arc([ex1 - 14, by - 6, ex1 + 14, by + 12], 180, 360, fill=ink, width=w)
        d.arc([ex2 - 14, by - 6, ex2 + 14, by + 12], 180, 360, fill=ink, width=w)
    elif mode == "surprised":
        d.line([ex1 - 13, by - 6, ex1 + 13, by - 6], fill=ink, width=w)
        d.line([ex2 - 13, by - 6, ex2 + 13, by - 6], fill=ink, width=w)
    else:
        d.line([ex1 - 13, by, ex1 + 13, by], fill=ink, width=w)
        d.line([ex2 - 13, by, ex2 + 13, by], fill=ink, width=w)


def _eyes(d, look, mode, ey=34, ex1=48, ex2=80, er=12):
    ink = _INK + (255,)
    if mode == "dead":
        for ex in (ex1, ex2):
            d.line([ex - 8, ey - 8, ex + 8, ey + 8], fill=ink, width=5)
            d.line([ex - 8, ey + 8, ex + 8, ey - 8], fill=ink, width=5)
        return
    wide = mode == "surprised"
    rr = er + (2 if wide else 0)
    pr = 5 if wide else 7
    psx, psy = 6 * look, (4 if mode == "sad" else 0)
    for ex in (ex1, ex2):
        d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=_CREAM + (255,), outline=ink, width=2)
        d.ellipse([ex + psx - pr, ey + psy - pr, ex + psx + pr, ey + psy + pr], fill=ink)
        d.ellipse([ex + psx - pr + 1, ey + psy - pr + 1, ex + psx - pr + 4, ey + psy - pr + 4],
                  fill=_CREAM + (255,))


def _mouth(d, kind, mx=64, my=70, R=18):
    ink = _INK + (255,)
    if kind == "bigsmile":
        d.chord([mx - R - 2, my - R, mx + R + 2, my + R], 0, 180, fill=ink)
    elif kind == "smile":
        d.chord([mx - R, my - R, mx + R, my + R], 18, 162, fill=ink)
    elif kind == "frown":
        d.chord([mx - R, my - R + 8, mx + R, my + R + 8], 200, 340, fill=ink)
    elif kind == "o":
        d.ellipse([mx - R + 2, my - R, mx + R - 2, my + R], fill=ink)
    elif kind == "grit":
        d.rounded_rectangle([mx - R, my - 6, mx + R, my + 6], radius=3, fill=ink)
        for tx in range(mx - R + 4, mx + R, 7):
            d.line([tx, my - 6, tx, my + 6], fill=_GREEN + (255,), width=2)
    else:
        d.rounded_rectangle([mx - R, my - 3, mx + R, my + 3], radius=2, fill=ink)


def make_face(w, h, tier, look, expr):
    """Token-LOGO face (rounded square + hole-as-mouth + base ellipse), rendered
    at high res then downscaled. Eyes glance L/C/R, brows + mouth swing happy ->
    sad -> angry, cracks deepen with damage. expr drives the reactive states."""
    S = 128
    img = Image.new("RGBA", (S, S), _BG + (255,))
    d = ImageDraw.Draw(img)

    if expr == "god":
        head = _LIME
    elif expr == "dead":
        head = tuple(int(c * 0.5) for c in _GREEN)
    else:
        head = tuple(int(c * (1.0 - 0.10 * min(tier, 4))) for c in _GREEN)

    # token-logo head: rounded square + detached base ellipse
    d.rounded_rectangle([14, 4, 114, 92], radius=24, fill=head + (255,),
                        outline=_CREAM + (255,), width=4)
    d.ellipse([46, 96, 82, 112], fill=head + (255,), outline=_CREAM + (255,), width=3)

    if expr in ("god", "grin"):
        brow, eyem, mouth = "happy", "normal", "bigsmile"
    elif expr in ("rampage", "hurt"):
        brow, eyem, mouth = "angry", "normal", "grit"
    elif expr == "ouch":
        brow, eyem, mouth = "surprised", "surprised", "o"
    elif expr == "dead":
        brow, eyem, mouth = "sad", "dead", "frown"
    else:
        brow = ("happy", "neutral", "sad", "sad", "sad")[min(tier, 4)]
        eyem = "sad" if tier >= 3 else "normal"
        mouth = ("smile", "o", "flat", "frown", "frown")[min(tier, 4)]

    _brows(d, brow)
    _eyes(d, look, eyem)
    _mouth(d, mouth)

    # hurt blush + sad tear
    if expr in ("hurt", "rampage") or (expr == "normal" and tier >= 2):
        d.ellipse([32, 58, 44, 70], fill=_PINK + (255,))
        d.ellipse([84, 58, 96, 70], fill=_PINK + (255,))
    if (expr == "normal" and tier >= 3) or expr == "dead":
        d.ellipse([41, 46, 50, 64], fill=_BLUE + (255,))

    # bold cracks (dark with a cream highlight so they read at HUD size)
    ncr = 5 if expr == "dead" else min(tier, 4)
    for i in range(min(ncr, len(_CRACKS))):
        pts = [(x * S, y * S) for (x, y) in _CRACKS[i]]
        d.line(pts, fill=_INK + (255,), width=8, joint="curve")
        d.line([(x + 2, y + 1) for (x, y) in pts], fill=_CREAM + (255,), width=2, joint="curve")

    return img.resize((max(1, w), max(1, h)), Image.LANCZOS)


def build_faces(wad):
    """Replace every STF* face lump with an animated Token smiley keyed to the
    face state encoded in its name (pain tier + glance direction + expression).
    GZDoom cycles these automatically -> the eyes glance around, the mouth
    grins on pickups, grimaces while firing, and frowns as health drops."""
    n = 0
    for name in set(wad.names_with_prefix("STF")):
        raw = wad.read(name)
        try:
            w, h, lo, to = struct.unpack("<hhhh", raw[:8])
        except struct.error:
            continue
        if not (0 < w <= 64 and 0 < h <= 64):
            continue
        if name.startswith("STFB"):   # not a standard face state
            continue
        expr, look = "normal", 0
        dm = re.search(r"(\d)", name)
        tier = int(dm.group(1)) if dm else 0
        if name.startswith("STFDEAD"):
            expr, tier = "dead", 4
        elif name.startswith("STFGOD"):
            expr, tier = "god", 0
        elif name.startswith("STFEVL"):
            expr = "grin"
        elif name.startswith("STFKILL"):
            expr = "rampage"
        elif name.startswith("STFOUCH"):
            expr = "ouch"
        elif name.startswith("STFTR"):
            expr, look = "hurt", 1
        elif name.startswith("STFTL"):
            expr, look = "hurt", -1
        elif name.startswith("STFST") and len(name) >= 7 and name[6].isdigit():
            tier = int(name[5])
            look = (1, 0, -1)[int(name[6])] if int(name[6]) < 3 else 0
        face = make_face(w, h, min(tier, 4), look, expr)
        save_sprite(face, name, GRAPHICS, lo, to)
        n += 1
    return n


def save_plain(img, name, folder):
    img.save(os.path.join(folder, name + ".png"))


def build_titles():
    """TOKEN DOOM title screen (TITLEPIC) + plain-text menu logo (M_DOOM)."""
    title = "TOKEN DOOM"
    bg = pal.hex_rgb("#03251e")
    green = pal.hex_rgb("#17d079")
    cream = pal.hex_rgb("#f5f4ea")
    lime = pal.hex_rgb("#cff851")

    # TITLEPIC: 320x200 fullscreen
    W, H = 320, 200
    img = Image.new("RGBA", (W, H), bg + (255,))
    mark = get_mark()
    mh = 84
    mw = int(mark.width * (mh / mark.height))
    m = tint_mask(mark.resize((mw, mh)), green)
    img.alpha_composite(m, ((W - mw) // 2, 22))
    d = ImageDraw.Draw(img)
    f1 = load_font(40)
    tw, th = text_wh(title, f1)
    d.text(((W - tw) // 2, 124), title, fill=cream + (255,), font=f1)
    f2 = load_font(12)
    sub = "A Token Security joint"
    sw, _ = text_wh(sub, f2)
    d.text(((W - sw) // 2, 176), sub, fill=lime + (255,), font=f2)
    save_plain(img, "TITLEPIC", GRAPHICS)

    # M_DOOM: plain-text menu header (transparent)
    f3 = load_font(28)
    tw3, th3 = text_wh(title, f3)
    menu = Image.new("RGBA", (tw3 + 8, th3 + 8), (0, 0, 0, 0))
    dd = ImageDraw.Draw(menu)
    dd.text((4, 2), title, fill=green + (255,), font=f3)
    save_plain(menu, "M_DOOM", GRAPHICS)


# Skill-menu graphics -> themed difficulty names (more access = more dangerous)
SKILL_NAMES = {
    "M_JKILL": "Read Only",
    "M_ROUGH": "Least Privilege",
    "M_HURT": "Standing Access",
    "M_ULTRA": "Over-Privileged",
    "M_NMARE": "Full Admin",
}


def build_menu():
    green = pal.hex_rgb("#17d079")
    for lump, text in SKILL_NAMES.items():
        f = load_font(18)
        tw, th = text_wh(text, f)
        img = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((4, 2), text, fill=green + (255,), font=f)
        save_plain(img, lump, GRAPHICS)


def main():
    print("Loading WAD:", WAD_PATH)
    wad = wadlib.WAD(WAD_PATH)
    rmap = pal.remap_base(wadlib.base_palette(wad))

    print("Palette:")
    build_palette(wad)

    print("Monsters:")
    mn = build_labeled(wad, rmap, MONSTERS, SPRITES, mode="below")
    print(f"  {mn} monster frames")

    print("Weapons (held):")
    wn = build_labeled(wad, rmap, WEAPONS, SPRITES, mode="overlay")
    print(f"  {wn} held weapon frames")

    print("Weapons (ground):")
    gn = build_labeled(wad, rmap, WEAPON_PICKUPS, SPRITES, mode="below")
    print(f"  {gn} ground pickup frames")

    print("Powerups:")
    pn = build_powerups()
    print(f"  {pn} powerup sprites")

    print("Faces:")
    fn = build_faces(wad)
    print(f"  {fn} face frames")

    print("Titles:")
    build_titles()
    print("  TITLEPIC + M_DOOM")

    print("Menu:")
    build_menu()
    print(f"  {len(SKILL_NAMES)} difficulty labels")

    print("Done.")


if __name__ == "__main__":
    main()
