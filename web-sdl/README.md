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
  resize) but replaces the file-picker UI with a Token splash that auto-loads one
  merged IWAD into Emscripten MEMFS and boots PrBoom with `-iwad token-doom.wad`.
- `token-doom.wad` here is the merged IWAD (shareware E1 + our overrides), the
  same artifact as `../web/assets/token-doom-web.wad`. We don't overlay a PWAD:
  the mirror-split sprites would collide with the shareware IWAD's combined
  rotation lumps (PrBoom rejects two lumps per rotation), so the combined lumps
  are dropped inside the merged IWAD. PrBoom still reads the IWAD's DEHACKED lump,
  so pickup-message renames apply.

Prebuilt engine files (`index.js`, `index.wasm`, `index.data`) are from
dwasm.m-h.org.uk. `index.data` bundles PrBoom's helper `prboomx.wad`.

## Rebuild the WAD

```
python build/make_wad.py                           # dist/token-doom.wad (vanilla PWAD)
MODE=merge IWAD_PATH=web-sdl/doom1.wad \
  OUT_WAD=web/assets/token-doom-web.wad python build/make_wad.py
cp web/assets/token-doom-web.wad web-sdl/token-doom.wad
```

`web-sdl/doom1.wad` is the source shareware IWAD, kept only as the merge input
(the page does not fetch it).

## vs the other build (`../web/`)

| | `../web/` (doom.wasm) | this (`web-sdl/`, Dwasm) |
|---|---|---|
| Mouse | faked turn via key taps | real analog turning |
| Sound | none | yes |
| WAD | single merged IWAD | single merged IWAD |
| DEHACKED renames | ignored | applied |
| Engine size | ~4.5 MB | ~3 MB (wasm+data) |
| Headers | none | none |

This build is the better player experience. The doom.wasm build is kept as a
lighter fallback.
