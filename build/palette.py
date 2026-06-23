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


def remap_base(orig256):
    """Map each of the 256 base colors to its nearest brand color."""
    return [nearest_brand(c) for c in orig256]


def remap_playpal_lump(raw):
    """Remap every color in the full PLAYPAL lump (all 14 sub-palettes)."""
    out = bytearray(len(raw))
    for i in range(len(raw) // 3):
        r, g, b = raw[i * 3], raw[i * 3 + 1], raw[i * 3 + 2]
        nr, ng, nb = nearest_brand((r, g, b))
        out[i * 3], out[i * 3 + 1], out[i * 3 + 2] = nr, ng, nb
    return bytes(out)
