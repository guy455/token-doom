#!/bin/bash
# TOKEN DOOM - macOS launcher. Everything is bundled; just run this.
cd "$(dirname "$0")"

# Unpack the bundled GZDoom on first run (macOS unzip preserves app permissions).
if [ ! -d "GZDoom.app" ]; then
  echo "First run: setting up GZDoom..."
  unzip -q gzdoom-macos.zip
fi

# Clear the downloaded-file quarantine so GateKeeper doesn't block launch.
xattr -dr com.apple.quarantine GZDoom.app 2>/dev/null
xattr -d com.apple.quarantine doom.wad token-doom.pk3 2>/dev/null

"./GZDoom.app/Contents/MacOS/gzdoom" -iwad "./doom.wad" -file "./token-doom.pk3" -config "./token-doom.ini"
