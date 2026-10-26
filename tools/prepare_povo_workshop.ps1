param(
    [string]$CS2Root = 'C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$mapName = 'trento_povo_campus'
$package = Join-Path $projectRoot "build\package\$mapName.vpk"
$overview = Join-Path $projectRoot "exports\povo_campus\radar\$mapName.txt"
$gameAddons = Join-Path $CS2Root 'game\csgo_addons'
if (!(Test-Path -LiteralPath $gameAddons -PathType Container)) {
    throw "CS2 addons directory is missing: $gameAddons"
}
if (!(Test-Path -LiteralPath $package -PathType Leaf)) {
    throw 'No completed campus package exists. Finish the map build first.'
}
$addon = Join-Path $gameAddons 'trento_povo_friends'
$staging = Join-Path $projectRoot 'build\workshop'
New-Item -ItemType Directory -Force -Path (Join-Path $addon 'maps'), (Join-Path $addon 'cfg'), $staging | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $CS2Root 'content\csgo_addons\trento_povo_friends') | Out-Null
$destination = Join-Path $addon "maps\$mapName.vpk"
Copy-Item -LiteralPath $package -Destination $destination -Force
& python (Join-Path $PSScriptRoot 'verify_cs2_package.py') $destination --map $mapName --model povo1_campus --overview $overview --full-crc --report (Join-Path $staging 'package-check.json')
if ($LASTEXITCODE -ne 0) { throw 'Workshop snapshot failed package verification. Do not publish it.' }
Set-Content -LiteralPath (Join-Path $addon 'addoninfo.txt') -Encoding ascii -Value '"AddonInfo" { "IsTemplate" "0" "IsPlayable" "1" }'
Copy-Item -LiteralPath (Join-Path $projectRoot 'config\multiplayer\povo_duel.cfg') -Destination (Join-Path $addon 'cfg\povo_duel.cfg') -Force
Copy-Item -LiteralPath (Join-Path $projectRoot 'config\multiplayer\workshop_description.txt') -Destination (Join-Path $staging 'description.txt') -Force
Copy-Item -LiteralPath (Join-Path $projectRoot 'exports\povo_campus\runtime\exterior_road_under_bridge_0000.png') -Destination (Join-Path $staging 'preview.png') -Force
$sourceInfo = Get-Item -LiteralPath $package
$sourceHash = (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash
$stagedHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
if ($sourceHash -ne $stagedHash) { throw 'The build package changed while staging. Rerun after compilation finishes.' }
[ordered]@{
    addon = 'trento_povo_friends'
    sourcePackage = $sourceInfo.FullName
    sourceLastWriteTimeUtc = $sourceInfo.LastWriteTimeUtc.ToString('o')
    packageSha256 = $stagedHash
    bytes = $sourceInfo.Length
    stagedAtUtc = [DateTime]::UtcNow.ToString('o')
    visibility = 'Friends only'
    published = $false
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $staging 'snapshot.json') -Encoding ascii
Write-Host "Prepared addon: $addon"
Write-Host "Source package timestamp (UTC): $($sourceInfo.LastWriteTimeUtc.ToString('u'))"
Write-Host "Preview and description: $staging"
Write-Host 'This stages the last completed package. Rerun AFTER the new build finishes before publishing.'
Write-Host 'Workshop Manager: New > trento_povo_friends > Classic + Wingman > Friends only.'
Write-Host 'No Workshop upload has been performed.'
