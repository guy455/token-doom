"""Token brand palette + nearest-color remap of DOOM's PLAYPAL."""

BRAND_HEX = [
    "#17d079", "#20d27e", "#3cc982", "#25654a", "#00352a", "#03251e", "#0e1914",
    "#f5f4ea", "#cff851", "#eecc1d", "#7367ff", "#f3bfbf", "#002957", "#06d495",
    "#4c73ff", "#3d5ccc", "#2f479d", "#809cff", "#edf1ff",
]


def hex_rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


BRAND = [hex_rgb(h) for h in BRAND_HEX]


def nearest_brand(rgb, _cache={}):
    if rgb in _cache:
        return _cache[rgb]
    r, g, b = rgb
    best, bd = BRAND[0], 1e18
    for c in BRAND:
        d = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2
        if d < bd:
            bd, best = d, c
    _cache[rgb] = best
    return best


# How hard to push colors toward the brand palette (1.0 = full snap, dark/high
# contrast; lower = keep more original brightness). Sprites are pushed harder
# than the world so monsters/weapons read as branded without darkening levels.
TINT_SPRITE = 0.8   # monster / weapon recolor
TINT_WORLD = 0.5    # global PLAYPAL (walls, floors, untouched things)


def blend(rgb, t, _cache={}):
    """Blend a color toward its nearest brand color by strength t."""
    key = (rgb, t)
    if key in _cache:
        return _cache[key]
    br, bg, bb = nearest_brand(rgb)
    r, g, b = rgb
    out = (int(r + (br - r) * t), int(g + (bg - g) * t), int(b + (bb - b) * t))
    _cache[key] = out
    return out


def remap_base(orig256):
    """Tint the 256 base colors toward brand (sprite strength)."""
    return [blend(c, TINT_SPRITE) for c in orig256]


def remap_playpal_lump(raw):
    """Tint every color in the full PLAYPAL lump (world strength)."""
    out = bytearray(len(raw))
    for i in range(len(raw) // 3):
        r, g, b = raw[i * 3], raw[i * 3 + 1], raw[i * 3 + 2]
        nr, ng, nb = blend((r, g, b), TINT_WORLD)
        out[i * 3], out[i * 3 + 1], out[i * 3 + 2] = nr, ng, nb
    return bytes(out)
