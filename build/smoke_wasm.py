"""Headless boot test for the browser build.

Drives web/assets/doom.wasm with wasmtime exactly like the browser page does:
feeds the shareware IWAD + token-doom.wad PWAD through the loading.* imports,
pumps tickGame, captures the engine's stdout, and saves framebuffer PNGs so we
can confirm the mod actually renders (recolored title + sprites) without a
browser. Pure verification, not shipped.
"""
import os
import struct
import sys

from PIL import Image
from wasmtime import Engine, Store, Module, Linker, FuncType, ValType

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web", "assets")
SHOT = os.path.join(HERE, "__pycache__")  # scratch for the PNGs

MODE = os.environ.get("MODE", "mod")
if MODE == "single":
    # Inject one pre-merged IWAD (no PWAD overlay).
    wads = [open(os.environ.get("WADFILE", os.path.join(WEB, "token-doom.wad")), "rb").read()]
else:
    iwad = open(os.path.join(WEB, "doom1.wad"), "rb").read()
    pwad = open(os.environ.get("WADFILE", os.path.join(WEB, "token-doom.wad")), "rb").read()
    wads = [iwad] if MODE == "iwad" else [iwad, pwad]
total = sum(len(w) for w in wads)
print(f"MODE={MODE} wads={len(wads)} total={total}", flush=True)

engine = Engine()
store = Store(engine)
module = Module.from_file(engine, os.path.join(WEB, "doom.wasm"))
linker = Linker(engine)

mem = None
fb_w = fb_h = 0
clock = [0]
frames = {}
infos = []
errors = []

I32 = ValType.i32()
I64 = ValType.i64()


def read_str(ptr, n):
    return bytes(mem.read(store, ptr, ptr + n)).decode("utf-8", "ignore")


def on_info(ptr, n):
    s = read_str(ptr, n)
    infos.append(s)
    sys.stderr.write(s)
    sys.stderr.flush()


def on_error(ptr, n):
    s = read_str(ptr, n)
    errors.append(s)
    sys.stderr.write("ERR:" + s)
    sys.stderr.flush()


def on_game_init(w, h):
    global fb_w, fb_h
    fb_w, fb_h = w, h


def wad_sizes(num_ptr, total_ptr):
    mem.write(store, struct.pack("<i", len(wads)), num_ptr)
    mem.write(store, struct.pack("<i", total), total_ptr)


def read_wads(dst_ptr, lens_ptr):
    off = dst_ptr
    for i, w in enumerate(wads):
        mem.write(store, w, off)
        off += len(w)
        mem.write(store, struct.pack("<i", len(w)), lens_ptr + i * 4)


def draw_frame(ptr):
    # Stash a couple of frames of interest (title, later demo).
    t = clock[1] if len(clock) > 1 else 0
    if t in WANT and t not in frames:
        raw = bytes(mem.read(store, ptr, ptr + fb_w * fb_h * 4))
        frames[t] = (fb_w, fb_h, raw)


def time_ms():
    # Advance on every call so any internal busy-wait loop makes progress.
    clock[0] += 2
    return clock[0]


WANT = {8, 600}

linker.define_func("console", "onInfoMessage", FuncType([I32, I32], []), on_info)
linker.define_func("console", "onErrorMessage", FuncType([I32, I32], []), on_error)
linker.define_func("loading", "onGameInit", FuncType([I32, I32], []), on_game_init)
linker.define_func("loading", "wadSizes", FuncType([I32, I32], []), wad_sizes)
linker.define_func("loading", "readWads", FuncType([I32, I32], []), read_wads)
linker.define_func("ui", "drawFrame", FuncType([I32], []), draw_frame)
linker.define_func("runtimeControl", "timeInMilliseconds", FuncType([], [I64]), time_ms)
linker.define_func("gameSaving", "sizeOfSaveGame", FuncType([I32], [I32]), lambda p: 0)
linker.define_func("gameSaving", "readSaveGame", FuncType([I32, I32], [I32]), lambda p, n: 0)
linker.define_func("gameSaving", "writeSaveGame", FuncType([I32, I32, I32], [I32]), lambda p, n, m: 0)

instance = linker.instantiate(store, module)
ex = instance.exports(store)
mem = ex["memory"]

clock.append(0)  # clock[1] = current tick index, for draw_frame
try:
    ex["initGame"](store)
except Exception as e:
    sys.stderr.write(f"\n[initGame trapped: {e}]\n")
    print("\n--- captured stdout before trap ---")
    print("".join(infos))
    print("--- captured stderr before trap ---")
    print("".join(errors))
    raise

tick = ex["tickGame"]
for t in range(max(WANT) + 5):
    clock[1] = t
    clock[0] += 28  # nudge real game-time forward so the attract demo starts
    tick(store)

print("=== engine stdout (first 40 lines) ===")
joined = "".join(infos).splitlines()
for line in joined[:40]:
    print(line)
if errors:
    print("=== engine STDERR ===")
    print("".join(errors))

print(f"\nframebuffer: {fb_w}x{fb_h}, frames captured: {sorted(frames)}")
for t, (w, h, raw) in frames.items():
    img = Image.frombytes("RGBA", (w, h), raw)
    b, g, r, a = img.split()
    img = Image.merge("RGBA", (r, g, b, a))  # BGRA -> RGBA
    out = os.path.join(SHOT, f"smoke_frame_{t}.png")
    img.convert("RGB").save(out)
    print("saved", out)

# A blank/black frame means nothing rendered; report mean luminance as a guard.
for t, (w, h, raw) in frames.items():
    nonblack = sum(1 for i in range(0, len(raw), 4) if raw[i] or raw[i + 1] or raw[i + 2])
    print(f"frame {t}: {nonblack}/{w*h} non-black pixels")

sys.exit(1 if errors else 0)
