param(
    [string]$CS2Root = 'C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive',
    [ValidateRange(640,7680)][int]$Width = 960,
    [ValidateRange(480,4320)][int]$Height = 600,
    [switch]$Match,
    [switch]$Fly,
    [switch]$Windowed,
    [switch]$Winter
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$mapName = if ($Winter) { 'trento_povo_campus_winter' } else { 'trento_povo_campus' }
$package = Join-Path $projectRoot "build\package\$mapName.vpk"
$executable = Join-Path $CS2Root 'game\bin\win64\cs2.exe'
if (!(Test-Path -LiteralPath $package)) { throw 'Build the campus first: python tools/cs2_campus.py' }
if (!(Test-Path -LiteralPath $executable)) { throw "CS2 not found at $CS2Root. Pass -CS2Root with your Steam installation path." }
if (Get-Process cs2 -ErrorAction SilentlyContinue) { throw 'Close CS2, then run play_campus.cmd again.' }
& python (Join-Path $PSScriptRoot 'verify_cs2_package.py') $package --map $mapName --model povo1_campus --overview (Join-Path $projectRoot "exports\povo_campus\radar\$mapName.txt") --full-crc
if ($LASTEXITCODE -ne 0) { throw 'Campus package verification failed.' }
# This dedicated addon contains only the self-contained package and metadata.
$addon = Join-Path $CS2Root 'game\csgo_addons\trento_povo_campus_test'
New-Item -ItemType Directory -Force -Path (Join-Path $addon 'maps') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $CS2Root 'content\csgo_addons\trento_povo_campus_test') | Out-Null
Copy-Item -LiteralPath $package -Destination (Join-Path $addon "maps\$mapName.vpk") -Force
Set-Content -LiteralPath (Join-Path $addon 'addoninfo.txt') -Encoding ascii -Value '"AddonInfo" { "IsTemplate" "0" "IsPlayable" "1" }'
$launchArguments = @(
    '-steam','-retail','-addon','trento_povo_campus_test','-tools','-insecure','-condebug',
    '-vconsole','-netconport','27400',
    '+game_type','0','+game_mode','2','+map',"maps/$mapName.vpk"
)
if ($Windowed) { $launchArguments += @('-windowed','-w',"$Width",'-h',"$Height") }
if (!$Match) {
    # Prevent combat while the map loads; the helper reapplies settings after
    # map/gamemode configuration and automatically joins the ground-floor team.
    $launchArguments += @('+bot_quota','0','+mp_warmup_pausetimer','1')
}
Start-Process -FilePath $executable -WorkingDirectory (Split-Path -Parent $executable) -ArgumentList $launchArguments
if (!$Match) {
    $exploreArguments = @((Join-Path $PSScriptRoot 'cs2_explore.py'), '--map', $mapName, '--timeout', '180', '--log', (Join-Path $projectRoot 'build\gameplay\campus-explore.log'))
    if ($Fly) { $exploreArguments += '--fly' }
    & python @exploreArguments
    if ($LASTEXITCODE -ne 0) { throw 'Automatic exploration setup failed. See build/gameplay/campus-explore.log.' }
}
