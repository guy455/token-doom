# Token DOOM

DOOM, reskinned as a Token Security marketing piece. The whole game is recolored
to the Token palette, the monsters are renamed after the risks Token hunts (NHIs,
shadow AI, MCP servers, rogue tokens), the weapons become Token capabilities, and
the player's face is the Token logo that cracks and frowns as you take damage.

Episode 1, no new levels. Runs on GZDoom. Rudimentary on purpose.

![Title](docs/title.png)

## Download and play

No install. Download, unzip, double-click.

- **Windows** → [token-doom-windows.zip](https://github.com/guy455/token-doom/releases/download/v0.5/token-doom-windows.zip) → run `Play.bat`
- **macOS** (Apple Silicon + Intel) → [token-doom-macos.zip](https://github.com/guy455/token-doom/releases/download/v0.5/token-doom-macos.zip) → run `Play.command`

Everything is bundled: the engine, the game data, and the mod. Latest builds are
always on the [releases page](https://github.com/guy455/token-doom/releases/latest).

## What's in it

**The player face** is the Token logo, fully animated: eyes glance around, it
grins on a pickup, grimaces while firing, and cracks + frowns as health drops.

![Faces](docs/faces.png)

**Monsters** keep their shapes, wear the Token palette, and carry a name tag:

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

**Weapons** are Token capabilities, named on the gun and the pickup: Finder
(fist), Secret Scanner (pistol), Owner Establisher (shotgun), Campaign Creator
(chaingun), Playbook Launcher (rockets), Auto Remediator (plasma), Enzo (BFG).

**Difficulties** are access levels — more access, more danger:

![Difficulties](docs/difficulties.png)

**Powerups** are text boxes; health/armor/ammo pickups carry Token-flavored
messages.

## Build from source

The repo ships the recipe, not the copyrighted Doom art. The build script reads
sprites from a local `doom.wad`, recolors and labels them, and writes the mod.

```
python build/generate_assets.py     # reads D:\Downloads\doom.wad -> src/
# zip src/ into dist/token-doom.pk3, then:
tools/gzdoom/gzdoom.exe -iwad doom.wad -file dist/token-doom.pk3
```

`build/make_release.ps1` assembles the Windows + macOS download bundles.

Palette strength lives in `build/palette.py` (`TINT_SPRITE`, `TINT_WORLD`).
Names, faces, and difficulty labels live in `build/generate_assets.py`.

## Legal

GZDoom is GPL. The Token branding and generated art are Token's own. The base
Doom game data is id Software's and is bundled here for internal use only — not
for public redistribution.
