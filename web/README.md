# Token DOOM - web build

Plays in a browser, no install. Static files only: an HTML page, the `doom.wasm`
engine, and one combined WAD. Host the `web/` folder anywhere that serves static
files.

## Run locally

```
python -m http.server 8753 --directory web
# open http://127.0.0.1:8753/
```

Click the screen to focus and capture the mouse, then: WASD move (A/D strafe),
mouse turns, click fires, right-click uses, 1-7 switch weapons, Esc opens the
menu / releases the mouse. Arrow keys also work.

The canvas scales to fill the viewport. Doom renders internally at 320x200, so
the look stays pixelated no matter the display size; making the canvas bigger is
the only readability lever this engine offers.

## How it works

- Engine: [jacobenget/doom.wasm](https://github.com/jacobenget/doom.wasm) v0.1.0,
  a doomgeneric/Chocolate-class vanilla engine. `index.html` instantiates it and
  injects the WAD bytes through the `loading.wadSizes` / `loading.readWads`
  imports, draws frames to a canvas, and forwards keys.
- One combined WAD, not a PWAD overlay. This engine build traps on a second
  injected WAD, so `build/make_wad.py MODE=merge` folds our overrides into a
  single IWAD: it copies the freely redistributable shareware Episode 1 data and
  swaps in our recolored, relabeled lumps in place.

## Rebuild the WAD

After regenerating sprites (`python build/generate_assets.py`):

```
MODE=merge OUT_WAD=web/assets/token-doom-web.wad python build/make_wad.py
```

`make_wad.py` reads the shareware IWAD from `web/assets/doom1.wad` by default
(override with `IWAD_PATH`). It needs the PNG sprites + `PLAYPAL.lmp` in `src/`.

`build/smoke_wasm.py` is a headless boot check: it drives `doom.wasm` with
wasmtime exactly like the page does and saves framebuffer PNGs, so you can
confirm a build renders without opening a browser.

## Known gaps vs the desktop (GZDoom) build

- Pickup-message renames don't apply. They live in a `DEHACKED` lump, and this
  engine build doesn't auto-load embedded DEHACKED. Monster name tags and weapon
  labels still show (they're baked into the sprite art). The combined WAD ships
  the DEHACKED lump anyway, for an engine that does read it.
- Registered-only monster sprites (Cyberdemon, Spider, Cacodemon, etc.) aren't
  overridden, because shareware Episode 1 doesn't contain them and they never
  spawn in E1. All E1 monsters, weapons, faces, palette, and title are recolored.
- No sound yet (the engine has no audio in v0.1.0).
- No analog mouse-look. doom.wasm v0.1.0 exposes only keyboard input, so mouse
  turning is faked by translating pointer-lock movement into turn-key taps (fixed
  speed, not smooth). Mouse buttons fire/use natively. True analog mouse needs a
  different engine build (an SDL/Emscripten Chocolate Doom, e.g. cloudflare/doom-wasm).
- Internal resolution is fixed at 320x200 (vanilla). Can't be raised here; GZDoom
  can, but there's no browser GZDoom.
