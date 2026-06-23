# Token DOOM

A rudimentary, intentionally rough Token Security reskin of DOOM Episode 1, shipped as a GZDoom mod. Marketing / fun project.

## What it is
- DOOM E1 with Token branding: recolored to the Token palette, enemies and weapons relabeled with security concepts, text-box powerups, a Token-logo player face that cracks as you take damage.
- No new levels. Stock E1 maps, reskinned.

## Stack
- **Engine:** GZDoom 4.14.2 (portable, in `tools/`, gitignored)
- **Game data:** the user's own `doom.wad` (Ultimate DOOM IWAD) — NOT committed
- **Mod:** a PK3 (zip) built from `src/`, loaded on top of the IWAD
- **Asset pipeline:** Python + Pillow scripts in `build/` that read sprites from the WAD, recolor to the Token palette, bake labels, and emit PNGs into `src/sprites/`

## Scope (locked)
Monsters reskinned (recolor + name label, original shapes kept):
- Zombieman → NHI
- Shotgun Guy → Exposed Secrets
- Imp → AI Agent
- Demon → MCP Server
- Cacodemon → Shadow AI
- Lost Soul → unchanged

Weapons (recolor + name baked below sprite):
- Fist → Finder, Pistol → Secret Scanner, Shotgun → Owner Establisher,
  Chaingun → Campaign Creator, Rocket Launcher → Playbook Launcher,
  Plasma Gun → Auto Remediator, BFG → Enzo

Powerups: text-box sprites + custom pickup messages.
Player face: Token logo, cracking across 5 health tiers.
Palette: 19 Token brand colors; whole game remapped to nearest brand color (cohesive tint).

## Build
1. Generate assets: run `build/generate_assets.py` (reads `doom.wad`, writes `src/sprites/`).
2. Pack: zip `src/` contents into `dist/token-doom.pk3`.
3. Run: `tools/gzdoom/gzdoom.exe -iwad <doom.wad> -file dist/token-doom.pk3`

## Note on distribution
Building on the user's `doom.wad` is fine for local/dev use. A public marketing
giveaway built on id's original sprites would infringe id Software IP; for public
release the base would move to the BSD-licensed Freedoom IWAD (different monster
art). Decide at release time.
