# Token DOOM

The risks Token hunts, turned into things you can shoot.

It's DOOM Episode 1, recolored Token green, with every monster renamed after a
threat we kill for real: non-human identities, exposed secrets, rogue AI agents,
shadow AI, privilege escalation. The weapons are Token capabilities. The player's
face is the Token logo, and it cracks as your health drops.

## Play it now

**[Play Token DOOM in your browser](https://guy455.github.io/token-doom/)**

No install, no download. Mouse aims, WASD moves, click fires, sound on. Runs in
any modern browser.

![Title](docs/title.png)

## Screenshots

![Facing an Exposed Secrets enemy with the Secret Scanner](docs/gameplay-1.png)

![Clearing a room with the Auto Remediator](docs/gameplay-2.png)

![Out in the open, Token green everywhere](docs/gameplay-3.png)

## What you're fighting

**Monsters** keep their shapes, wear the Token palette, and carry a name tag over
their heads:

| Doom monster | Token name |
|---|---|
| Zombieman | NHI |
| Shotgun Guy | Exposed Secrets |
| Imp | AI Agent |
| Demon / Spectre | MCP Server |
| Cacodemon | Shadow AI |
| Lost Soul | Rogue Token |
| Baron of Hell | Privilege Escalation |
| Cyberdemon | Nation-State APT |
| Spider Mastermind | Rogue Superintelligence |

**Weapons** are Token capabilities, labeled on the gun: Finder (fist), Secret
Scanner (pistol), Auto Remediator (shotgun), Campaign Creator (chaingun),
Playbook Launcher (rockets), Owner Establisher (plasma), Enzo (BFG).

**The player face** is the Token logo, animated: eyes glance around, it grins on
a pickup, grimaces while firing, and cracks as health drops.

![Faces](docs/faces.png)

**Difficulties** are access levels: more access, more danger.

![Difficulties](docs/difficulties.png)

## Prefer a native build? Download for desktop

Bring your own Doom: drop a `doom.wad` (from a full copy of Doom on Steam or GOG,
or the free [freedoom1.wad](https://freedoom.github.io)) into the folder, then run
the launcher.

- Windows → [token-doom-windows.zip](https://github.com/guy455/token-doom/releases/latest/download/token-doom-windows.zip) → add `doom.wad`, run `Play.bat`
- macOS (Apple Silicon + Intel) → [token-doom-macos.zip](https://github.com/guy455/token-doom/releases/latest/download/token-doom-macos.zip) → add `doom.wad`, run `Play.command`

Latest builds are on the [releases page](https://github.com/guy455/token-doom/releases/latest).

## Build from source

The repo ships the recipe, not the copyrighted Doom art. `generate_assets.py`
reads sprites from a local `doom.wad`, recolors and labels them, and writes the
mod into `src/`:

```
python build/generate_assets.py          # doom.wad -> src/ (sprites, palette, labels)
python build/make_pk3.py                 # src/ -> dist/token-doom.pk3 (GZDoom desktop mod)
python build/make_wad.py                 # src/ -> dist/token-doom.wad (vanilla WAD)
powershell -File build/make_release.ps1  # Windows + macOS download bundles
```

The browser builds live in `web-sdl/` (PrBoom + SDL, mouse and sound) and `web/`
(doom.wasm, keyboard); see their READMEs to rebuild and deploy.
`build/make_web_deploy.py` assembles the hostable bundle.

Palette strength lives in `build/palette.py`. Names, faces, and labels live in
`build/generate_assets.py`.

## Legal

GZDoom and PrBoom are GPL. The Token branding and generated art are Token's own.
The browser version runs on id Software's freely redistributable Doom shareware
(Episode 1). The desktop downloads ship no Doom game data; you supply your own.
