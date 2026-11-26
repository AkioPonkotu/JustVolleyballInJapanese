param(
    [string]$GameDirectory = 'F:\SteamLibrary\steamapps\common\just volleyball'
)

# Read metadata only. Does not launch the game or attempt decryption.
$ErrorActionPreference = 'Stop'
$gameRoot = (Resolve-Path -LiteralPath $GameDirectory).Path
$pckPath = Join-Path $gameRoot 'volleyball.pck'
$stream = [IO.File]::OpenRead($pckPath)
$reader = [IO.BinaryReader]::new($stream)
try {
    if ($reader.ReadUInt32() -ne 0x43504447) {
        throw 'Not a standalone Godot PCK (GDPC signature missing).'
    }
    $formatVersion = $reader.ReadUInt32()
    if ($formatVersion -notin 2, 3, 4) {
        throw "Unsupported PCK header version: $formatVersion"
    }
    $engineVersion = '{0}.{1}.{2}' -f $reader.ReadUInt32(), $reader.ReadUInt32(), $reader.ReadUInt32()
    $flags = $reader.ReadUInt32()
    $fileBase = $reader.ReadUInt64()
    if ($formatVersion -ge 3) {
        $directoryOffset = $reader.ReadUInt64()
    } else {
        $directoryOffset = [uint64]96
    }
    if ($directoryOffset -gt ($stream.Length - 4)) {
        throw 'PCK directory offset is outside the file.'
    }
    $stream.Position = $directoryOffset
    $fileCount = $reader.ReadUInt32()
} finally {
    $reader.Dispose()
}

$files = @(Get-ChildItem -LiteralPath $gameRoot -File | Sort-Object Name | ForEach-Object {
    [ordered]@{
        name = $_.Name
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
})
[ordered]@{
    pck = [ordered]@{
        formatVersion = $formatVersion
        engineVersion = $engineVersion
        flags = $flags
        directoryEncrypted = [bool]($flags -band 1)
        relativeFileBase = [bool]($flags -band 2)
        sparseBundle = [bool]($flags -band 4)
        fileBase = $fileBase
        directoryOffset = $directoryOffset
        fileCount = $fileCount
    }
    files = $files
} | ConvertTo-Json -Depth 5
