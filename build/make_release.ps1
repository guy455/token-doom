# Builds self-contained Windows + macOS download bundles into dist/.
# Run from the repo root:  powershell -File build\make_release.ps1
$ErrorActionPreference = "Stop"
$proj = (Resolve-Path "$PSScriptRoot\..").Path
$dist = Join-Path $proj "dist"
$tools = Join-Path $proj "tools"
$pk3 = Join-Path $dist "token-doom.pk3"
$wad = "D:\Downloads\doom.wad"
$macZip = Join-Path $tools "gzdoom-macos.zip"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$bs = [char]92; $fw = [char]47

function New-Bundle($srcDir, $outZip) {
  if (Test-Path $outZip) { [System.IO.File]::Delete($outZip) }
  $fs = [System.IO.File]::Open($outZip, [System.IO.FileMode]::Create)
  $zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
  foreach ($f in (Get-ChildItem -Path $srcDir -Recurse -File)) {
    $rel = $f.FullName.Substring($srcDir.Length + 1).Replace($bs, $fw)
    $e = $zip.CreateEntry($rel, [System.IO.Compression.CompressionLevel]::Optimal)
    if ($f.Name -like "*.command") { $e.ExternalAttributes = 0x01ED0000 }  # unix 0755
    $o = $e.Open(); $b = [System.IO.File]::ReadAllBytes($f.FullName)
    $o.Write($b, 0, $b.Length); $o.Close()
  }
  $zip.Dispose(); $fs.Close()
  "{0}: {1:N1} MB" -f (Split-Path $outZip -Leaf), ((Get-Item $outZip).Length / 1MB)
}

# fetch macOS GZDoom once
if (-not (Test-Path $macZip)) {
  "Downloading GZDoom macOS build..."
  Invoke-WebRequest -Uri "https://github.com/ZDoom/gzdoom/releases/download/g4.14.2/gzdoom-4-14-2-macos.zip" -OutFile $macZip -UseBasicParsing
}

$stage = Join-Path $dist "stage"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }

# ---- Windows bundle ----
$win = Join-Path $stage "win"
New-Item -ItemType Directory -Force -Path $win | Out-Null
Copy-Item -Recurse (Join-Path $tools "gzdoom") (Join-Path $win "gzdoom")
Copy-Item $wad (Join-Path $win "doom.wad")
Copy-Item $pk3 (Join-Path $win "token-doom.pk3")
Copy-Item (Join-Path $proj "packaging\win\Play.bat") $win
Copy-Item (Join-Path $proj "packaging\win\README.txt") $win
New-Bundle $win (Join-Path $dist "token-doom-windows.zip")

# ---- macOS bundle ----
$mac = Join-Path $stage "mac"
New-Item -ItemType Directory -Force -Path $mac | Out-Null
Copy-Item $macZip (Join-Path $mac "gzdoom-macos.zip")
Copy-Item $wad (Join-Path $mac "doom.wad")
Copy-Item $pk3 (Join-Path $mac "token-doom.pk3")
Copy-Item (Join-Path $proj "packaging\mac\Play.command") $mac
Copy-Item (Join-Path $proj "packaging\mac\README.txt") $mac
New-Bundle $mac (Join-Path $dist "token-doom-macos.zip")

Remove-Item $stage -Recurse -Force
"Done."
