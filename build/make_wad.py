"""Pack src/ (PNG sprites + graphics, PLAYPAL, LANGUAGE) into a vanilla PWAD.

GZDoom eats the PK3 directly, but browser Doom engines (Chocolate / doomgeneric
class) are vanilla: they need a real WAD with Doom-format picture lumps, a raw
PLAYPAL, and a DEHACKED text lump instead of the ZDoom LANGUAGE lump.

This reuses the same src/ the PK3 build produces. It:
  - reads each PNG's grAb offset chunk (left/top offset),
  - quantizes RGBA pixels against the mod's remapped PLAYPAL,
  - encodes Doom picture lumps (posts, with transparency from alpha),
  - wraps sprites in S_START/S_END markers,
  - converts LANGUAGE -> a BEX [STRINGS] DEHACKED lump,
  - writes dist/token-doom.wad.

Run: python build/make_wad.py
"""
import os
import re
import struct

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
SPRITES = os.path.join(SRC, "sprites")
GRAPHICS = os.path.join(SRC, "graphics")
OUT = os.path.join(ROOT, "dist", "token-doom.wad")


# ---- PNG grAb offset reader ----------------------------------------------
def read_grab(png_bytes):
    """Return (xoff, yoff) from the PNG's grAb chunk, or (0, 0) if absent."""
    i = png_bytes.find(b"grAb")
    if i < 0:
        return 0, 0
    x, y = struct.unpack(">ii", png_bytes[i + 4:i + 12])
    return x, y


# ---- palette + nearest-colour quantizer ----------------------------------
def load_palette():
    with open(os.path.join(SRC, "PLAYPAL.lmp"), "rb") as f:
        raw = f.read(768)
    return [(raw[i * 3], raw[i * 3 + 1], raw[i * 3 + 2]) for i in range(256)]


class Quantizer:
    def __init__(self, palette):
        self.pal = palette
        self.cache = {}

    def index(self, rgb):
        hit = self.cache.get(rgb)
        if hit is not None:
            return hit
        r, g, b = rgb
        best, bestd = 0, 1 << 30
        for i, (pr, pg, pb) in enumerate(self.pal):
            d = (pr - r) ** 2 + (pg - g) ** 2 + (pb - b) ** 2
            if d < bestd:
                best, bestd = i, d
                if d == 0:
                    break
        self.cache[rgb] = best
        return best


# ---- PNG -> Doom picture lump --------------------------------------------
def encode_picture(img, xoff, yoff, q):
    """Encode an RGBA Image as a Doom picture lump. Alpha < 128 is transparent."""
    w, h = img.size
    px = img.load()
    columns = []
    for x in range(w):
        col = bytearray()
        y = 0
        while y < h:
            # skip transparent
            while y < h and px[x, y][3] < 128:
                y += 1
            if y >= h:
                break
            topdelta = y
            run = bytearray()
            while y < h and px[x, y][3] >= 128 and len(run) < 254:
                r, g, b, _ = px[x, y]
                run.append(q.index((r, g, b)))
                y += 1
            col.append(topdelta & 0xFF)       # topdelta
            col.append(len(run) & 0xFF)        # length
            col.append(run[0] if run else 0)   # unused leading pad
            col += run
            col.append(run[-1] if run else 0)  # unused trailing pad
        col.append(0xFF)                       # column terminator
        columns.append(bytes(col))

    header = struct.pack("<hhhh", w, h, xoff, yoff)
    table_size = 4 * w
    base = len(header) + table_size
    offsets = []
    running = base
    for c in columns:
        offsets.append(running)
        running += len(c)
    table = b"".join(struct.pack("<I", o) for o in offsets)
    return header + table + b"".join(columns)


# ---- LANGUAGE -> DEHACKED [STRINGS] --------------------------------------
def make_dehacked():
    lang = os.path.join(SRC, "LANGUAGE")
    pairs = []
    with open(lang, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("["):
                continue
            m = re.match(r'^([A-Z0-9_]+)\s*=\s*"(.*)"\s*;?\s*$', line)
            if m:
                pairs.append((m.group(1), m.group(2)))
    out = ["Patch File for DeHackEd v3.0", "Doom version = 19", "Patch format = 6",
           "", "[STRINGS]"]
    for k, v in pairs:
        out.append(f"{k} = {v}")
    out.append("")
    return "\n".join(out).encode("ascii", "ignore")


# ---- WAD writer -----------------------------------------------------------
def lump_name(filename):
    return os.path.splitext(filename)[0].upper()[:8]


def write_wad(lumps, path, magic=b"PWAD"):
    """lumps: ordered list of (name, bytes). Markers are ('S_START', b'')."""
    body = bytearray()
    directory = []
    for name, data in lumps:
        pos = 12 + len(body)
        body += data
        directory.append((pos, len(data), name))
    dirofs = 12 + len(body)
    header = struct.pack("<4sii", magic, len(lumps), dirofs)
    dirbytes = bytearray()
    for pos, size, name in directory:
        dirbytes += struct.pack("<ii8s", pos, size, name.encode("ascii")[:8].ljust(8, b"\x00"))
    with open(path, "wb") as f:
        f.write(header)
        f.write(body)
        f.write(dirbytes)


def main():
    pal = load_palette()
    q = Quantizer(pal)
    lumps = []
    skip_deh = os.environ.get("SKIP_DEH") == "1"
    skip_spr = os.environ.get("SKIP_SPRITES") == "1"
    skip_gfx = os.environ.get("SKIP_GFX") == "1"
    skip_pal = os.environ.get("SKIP_PAL") == "1"
    out_path = os.environ.get("OUT_WAD", OUT)

    # PLAYPAL (raw)
    if not skip_pal:
        with open(os.path.join(SRC, "PLAYPAL.lmp"), "rb") as f:
            lumps.append(("PLAYPAL", f.read()))

    # DEHACKED (string renames)
    if not skip_deh:
        lumps.append(("DEHACKED", make_dehacked()))

    # Graphics (title / face / menu) as global picture lumps
    gfx = sorted(os.listdir(GRAPHICS)) if not skip_gfx else []
    for fn in gfx:
        if not fn.lower().endswith(".png"):
            continue
        with open(os.path.join(GRAPHICS, fn), "rb") as f:
            raw = f.read()
        x, y = read_grab(raw)
        img = Image.open(os.path.join(GRAPHICS, fn)).convert("RGBA")
        lumps.append((lump_name(fn), encode_picture(img, x, y, q)))
    print(f"  graphics: {len(gfx)} lumps")

    # Sprites between S_START / S_END
    spr = sorted(os.listdir(SPRITES)) if not skip_spr else []
    if spr:
        lumps.append(("S_START", b""))
    n = 0
    for fn in spr:
        if not fn.lower().endswith(".png"):
            continue
        with open(os.path.join(SPRITES, fn), "rb") as f:
            raw = f.read()
        x, y = read_grab(raw)
        img = Image.open(os.path.join(SPRITES, fn)).convert("RGBA")
        lumps.append((lump_name(fn), encode_picture(img, x, y, q)))
        n += 1
    if spr:
        lumps.append(("S_END", b""))
    print(f"  sprites: {n} lumps")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if os.environ.get("MODE") == "merge":
        # The browser engine (doom.wasm v0.1.0) traps on a second injected WAD,
        # so instead of shipping a PWAD we fold our overrides into one combined
        # IWAD: copy every shareware lump, swap data in place for the names we
        # replace, and append DEHACKED. Names absent from shareware (registered-
        # only monsters that never spawn in Episode 1) are skipped.
        import wadlib
        iwad_path = os.environ.get("IWAD_PATH", os.path.join(ROOT, "web", "assets", "doom1.wad"))
        iw = wadlib.WAD(iwad_path)
        overrides = {name: data for (name, data) in lumps if data}

        # Our sprite override names (those between the S_START/S_END markers).
        spr_names, inblock = set(), False
        for name, data in lumps:
            if name in ("S_START", "SS_START"):
                inblock = True
            elif name in ("S_END", "SS_END"):
                inblock = False
            elif inblock:
                spr_names.add(name)
        # Sprite prefixes the shareware IWAD actually has (its sprite namespace).
        iw_spr_prefixes, inblock = set(), False
        for name, off, size in iw.lumps:
            if name in ("S_START", "SS_START"):
                inblock = True
            elif name in ("S_END", "SS_END"):
                inblock = False
            elif inblock:
                iw_spr_prefixes.add(name[:4])

        # A combined mirror lump (TROOA2A8) and our split single (TROOA2) would
        # both claim rotation 2, which vanilla rejects ("two lumps mapped to it").
        # Since we build this IWAD, drop each combined lump we've split.
        def replaced_combined(name):
            return (len(name) == 8 and name[:6] in overrides
                    and (name[:4] + name[6:8]) in overrides)

        merged, applied = [], set()
        for name, off, size in iw.lumps:
            if replaced_combined(name):
                continue
            if name in overrides and name not in applied:
                merged.append((name, overrides[name]))
                applied.add(name)
            else:
                merged.append((name, iw.data[off:off + size]))

        # Split-rotation lumps (e.g. POSSA8) aren't in the shareware IWAD as
        # separate names - the IWAD has the combined POSSA2A8. Insert ours into
        # the sprite namespace (before S_END) so they override the combined
        # lump's mirrored rotation. Only for sprites whose monster exists in
        # shareware; registered-only monsters stay skipped.
        new_sprites = [(n, overrides[n]) for n in overrides
                       if n not in applied and n in spr_names and n[:4] in iw_spr_prefixes]
        end_idx = next((i for i, (nm, _) in enumerate(merged) if nm in ("S_END", "SS_END")), len(merged))
        merged[end_idx:end_idx] = new_sprites
        for n, _ in new_sprites:
            applied.add(n)

        if "DEHACKED" in overrides:
            merged.append(("DEHACKED", overrides["DEHACKED"]))
            applied.add("DEHACKED")
        write_wad(merged, out_path, magic=b"IWAD")
        skipped = [n for n in overrides if n not in applied]
        size = os.path.getsize(out_path)
        print(f"Merged into {out_path} ({size} bytes, {len(merged)} lumps); "
              f"applied {len(applied)} overrides, skipped {len(skipped)} (not in shareware)")
    else:
        write_wad(lumps, out_path)
        size = os.path.getsize(out_path)
        print(f"Wrote {out_path} ({size} bytes, {len(lumps)} lumps)")


if __name__ == "__main__":
    main()
