param([string]$GameDirectory = 'F:\SteamLibrary\steamapps\common\just volleyball')
$ErrorActionPreference = 'Stop'
if (Get-Process -Name volleyball -ErrorAction SilentlyContinue) { throw 'Close Just Volleyball first.' }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' }
& uv run --python 3.12 --with-requirements (Join-Path $PSScriptRoot 'requirements.txt') python (Join-Path $PSScriptRoot 'patch_game.py') --game-dir $GameDirectory --package $PSScriptRoot --install
if ($LASTEXITCODE -ne 0) { throw 'Patch installation failed. Read the error above.' }
