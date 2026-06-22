"""Minimal DOOM WAD reader + Doom picture(sprite) decoder."""
import struct
from PIL import Image


class WAD:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        magic, numlumps, dirofs = struct.unpack("<4sii", self.data[:12])
        self.magic = magic.decode("ascii", "ignore")
        self.lumps = []        # ordered [(name, off, size)]
        self.index = {}        # name -> (off, size), last wins
        off = dirofs
        for _ in range(numlumps):
            lo, ls, raw = struct.unpack("<ii8s", self.data[off:off + 16])
            name = raw.split(b"\x00")[0].decode("ascii", "ignore").upper()
            self.lumps.append((name, lo, ls))
            self.index[name] = (lo, ls)
            off += 16

    def read(self, name):
        lo, ls = self.index[name.upper()]
        return self.data[lo:lo + ls]

    def names_with_prefix(self, prefix):
        p = prefix.upper()
        return [n for (n, lo, ls) in self.lumps if ls > 0 and n[:len(p)] == p]


def read_playpal_raw(wad):
    """Full PLAYPAL lump bytes (14 sub-palettes * 768)."""
    return wad.read("PLAYPAL")


def base_palette(wad):
    """First 256 RGB triplets of PLAYPAL."""
    raw = wad.read("PLAYPAL")
    return [(raw[i * 3], raw[i * 3 + 1], raw[i * 3 + 2]) for i in range(256)]


def decode_picture(raw, palette):
    """Decode a Doom picture lump to an RGBA Image using `palette` (256 RGB).
    Returns (image, leftoffset, topoffset)."""
    width, height, leftoff, topoff = struct.unpack("<hhhh", raw[:8])
    if width <= 0 or height <= 0:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0
    col_ofs = struct.unpack("<%di" % width, raw[8:8 + 4 * width])
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    px = img.load()
    for x in range(width):
        pos = col_ofs[x]
        while True:
            topdelta = raw[pos]; pos += 1
            if topdelta == 0xFF:
                break
            length = raw[pos]; pos += 1
            pos += 1  # unused pad byte
            for i in range(length):
                pi = raw[pos]; pos += 1
                y = topdelta + i
                if 0 <= y < height:
                    r, g, b = palette[pi]
                    px[x, y] = (r, g, b, 255)
            pos += 1  # unused trailing byte
    return img, leftoff, topoff
