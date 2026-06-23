"""Zip src/ into dist/token-doom.pk3 - the GZDoom desktop mod.

The desktop ("downloadable") build is just src/ packed as a PK3 (a zip GZDoom
reads). This is the same src/ that generate_assets.py produces, so every label /
name / title change lands here too. make_release.ps1 then bundles this PK3 with
the engine into the Windows/macOS download zips.

Run after generate_assets.py:  python build/make_pk3.py
"""
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "dist", "token-doom.pk3")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, _dirs, files in os.walk(SRC):
            for fn in sorted(files):
                full = os.path.join(dirpath, fn)
                arc = os.path.relpath(full, SRC).replace(os.sep, "/")
                z.write(full, arc)
                n += 1
    size = os.path.getsize(OUT)
    print(f"Wrote {OUT} ({size} bytes, {n} lumps)")


if __name__ == "__main__":
    main()
