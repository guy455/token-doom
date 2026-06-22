@echo off
REM Token DOOM launcher. Loads the mod on top of the local doom.wad.
set HERE=%~dp0
"%HERE%tools\gzdoom\gzdoom.exe" -iwad "D:\Downloads\doom.wad" -file "%HERE%dist\token-doom.pk3" -config "%HERE%tools\token-doom.ini"
