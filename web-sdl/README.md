# Token DOOM - web build (SDL engine: mouse + sound)

Second browser build, using a different engine than `../web/`. This one has
analog mouse-look and audio.

## Run locally

```
python -m http.server 8753 --directory .
# open http://127.0.0.1:8753/
```

Click Play. Mouse turns, click fires, right-click uses, WASD moves, 1-7 weapons,
Esc menu. Sound is on. F1 in-game shows the full key list.

## How it works

- Engine: prebuilt [GMH-Code/Dwasm](https://github.com/GMH-Code/Dwasm), a
  PrBoom+/PrBoomX WebAssembly build (SDL2). Single-threaded, so no COOP/COEP
  headers, plain static hosting works.
- `index.html` reproduces Dwasm's `Module` wiring (pointer lock, console toggle,
  resize) but replaces the file-picker UI with a Token splash that auto-loads two
  WADs into Emscripten MEMFS and boots PrBoom with `-iwad doom1.wad -file
  token-doom.wad`.
- `token-doom.wad` is the same vanilla PWAD the desktop pipeline produces
  (`dist/token-doom.wad`), loaded as an overlay. No merge needed: PrBoom is a Boom
  engine with full PWAD support, and it reads the DEHACKED lump, so pickup-message
  renames apply here (unlike the `../web/` doom.wasm build).

Prebuilt engine files (`index.js`, `index.wasm`, `index.data`) are from
dwasm.m-h.org.uk. `index.data` bundles PrBoom's helper `prboomx.wad`.

## Rebuild the PWAD

```
python build/make_wad.py                       # writes dist/token-doom.wad
cp dist/token-doom.wad web-sdl/token-doom.wad
```

(No `MODE=merge` here. The merged single-IWAD is only for the `../web/` doom.wasm
build, which can't take a second WAD.)

## vs the other build (`../web/`)

| | `../web/` (doom.wasm) | this (`web-sdl/`, Dwasm) |
|---|---|---|
| Mouse | faked turn via key taps | real analog turning |
| Sound | none | yes |
| WAD | single merged IWAD | IWAD + PWAD overlay |
| DEHACKED renames | ignored | applied |
| Engine size | ~4.5 MB | ~3 MB (wasm+data) |
| Headers | none | none |

This build is the better player experience. The doom.wasm build is kept as a
lighter fallback.
