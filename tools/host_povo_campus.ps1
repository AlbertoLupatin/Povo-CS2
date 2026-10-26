param(
    [string]$CS2Root = 'C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive',
    [switch]$SetupOnly
)
$ErrorActionPreference = 'Stop'
$profileSource = Join-Path (Split-Path -Parent $PSScriptRoot) 'config\multiplayer\povo_duel.cfg'
$cfgDirectory = Join-Path $CS2Root 'game\csgo\cfg'
$executable = Join-Path $CS2Root 'game\bin\win64\cs2.exe'
if (!(Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "CS2 not found at $CS2Root. Pass -CS2Root with your Steam installation path."
}
if (!(Test-Path -LiteralPath $cfgDirectory -PathType Container)) {
    throw "CS2 configuration directory is missing: $cfgDirectory"
}
Copy-Item -LiteralPath $profileSource -Destination (Join-Path $cfgDirectory 'povo_duel.cfg') -Force
foreach ($profileName in @('povo_ffa.cfg', 'povo_ffa_start.cfg')) {
    $ffaSource = Join-Path (Split-Path -Parent $PSScriptRoot) "config\multiplayer\$profileName"
    Copy-Item -LiteralPath $ffaSource -Destination (Join-Path $cfgDirectory $profileName) -Force
}
Write-Host 'Installed the Povo two-player match profile.'
Write-Host 'For free-for-all: exec povo_ffa_start, then after loading: exec povo_ffa'
Write-Host 'In normal CS2: Play > Workshop Maps > enable Open Party > start the Povo map.'
Write-Host 'Once the map has loaded, enter in the developer console: exec povo_duel'
Write-Host 'Your friend subscribes to the same Workshop item and joins through the Steam friends list.'
Write-Host 'Choose opposite teams. This PC hosts the match and must stay awake.'
if ($SetupOnly) { return }
if (Get-Process cs2 -ErrorAction SilentlyContinue) {
    Write-Host 'CS2 is already running. If this is a tools playtest, close it and launch normal CS2 through Steam.'
    return
}
# The existing solo launcher uses tools/insecure mode; friends hosting uses
# normal CS2 and the Workshop menu so Steam creates the joinable session.
Start-Process 'steam://rungameid/730'
