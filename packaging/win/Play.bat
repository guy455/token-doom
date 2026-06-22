@echo off
REM TOKEN DOOM - Windows. Everything is bundled; just run this.
set HERE=%~dp0
"%HERE%gzdoom\gzdoom.exe" -iwad "%HERE%doom.wad" -file "%HERE%token-doom.pk3" -config "%HERE%token-doom.ini"
