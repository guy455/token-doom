"""Assemble a clean, ready-to-host folder for the web (SDL) build.

Copies only the files the page actually serves into dist/web-deploy/ - drop that
folder on any static host (S3, an internal web server, Cloudflare/Vercel, etc.).
Leaves out build inputs (doom1.wad), the README, and the unused Dwasm helpers
(getgame.js / oly.js).

Run after the web-sdl WAD is rebuilt:  python build/make_web_deploy.py
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "web-sdl")
OUT = os.path.join(ROOT, "dist", "web-deploy")

FILES = ["index.html", "index.js", "index.wasm", "index.data", "token-doom.wad"]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    total = 0
    for fn in FILES:
        src = os.path.join(SRC, fn)
        if not os.path.exists(src):
            raise SystemExit(f"missing {src} - rebuild the web-sdl WAD first")
        shutil.copy2(src, os.path.join(OUT, fn))
        size = os.path.getsize(src)
        total += size
        print(f"  {fn:18} {size/1024:8.0f} KiB")
    print(f"Wrote {OUT} ({total/1024/1024:.1f} MB total)")


if __name__ == "__main__":
    main()
