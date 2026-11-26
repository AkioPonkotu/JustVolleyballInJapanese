param([string]$GameDirectory = 'F:\SteamLibrary\steamapps\common\just volleyball')
$ErrorActionPreference = 'Stop'
if (Get-Process -Name volleyball -ErrorAction SilentlyContinue) { throw 'Close Just Volleyball first.' }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv is required to restore the patch.' }
& uv run --python 3.12 --with-requirements (Join-Path $PSScriptRoot 'requirements.txt') python (Join-Path $PSScriptRoot 'patch_game.py') --game-dir $GameDirectory --package $PSScriptRoot --restore
if ($LASTEXITCODE -ne 0) { throw 'Patch restore failed. Read the error above.' }
