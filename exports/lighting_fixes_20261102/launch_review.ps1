$ErrorActionPreference = 'Stop'
$lightingReviewRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$lightingPython = Join-Path $lightingReviewRoot '.venv/Scripts/python.exe'
$lightingInstall = 'C:/Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive'
$lightingCandidate = Join-Path $lightingReviewRoot 'build/lighting-fixes-20261102/candidate.vpk'
if (!(Test-Path -LiteralPath $lightingCandidate)) { throw 'Candidate package is not ready' }
& $lightingPython (Join-Path $lightingReviewRoot 'tools/verify_cs2_package.py') $lightingCandidate --map trento_povo_campus --model povo1_campus --overview (Join-Path $lightingReviewRoot 'exports/povo_campus/radar/trento_povo_campus.txt') --full-crc --report (Join-Path $PSScriptRoot 'candidate-package-check.json')
if ($LASTEXITCODE -ne 0) { throw 'Candidate verification failed' }
if (Get-Process cs2 -ErrorAction SilentlyContinue) {
    & $lightingPython -c "from tools.playtest_povo_survey import Console,Driver; c=Console(27400); Driver(c,'trento_povo_campus').guard(); c.send('quit'); c.close()"
    if ($LASTEXITCODE -ne 0) { throw 'Solo-session guard rejected restart' }
    for ($lightingWait=0; $lightingWait -lt 160; $lightingWait++) {
        if (!(Get-Process cs2 -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Milliseconds 250
    }
    if (Get-Process cs2 -ErrorAction SilentlyContinue) { throw 'Previous game did not exit' }
}
$lightingAddon = Join-Path $lightingInstall 'game/csgo_addons/trento_povo_lighting_review'
New-Item -ItemType Directory -Force -Path (Join-Path $lightingAddon 'maps') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $lightingInstall 'content/csgo_addons/trento_povo_lighting_review') | Out-Null
Copy-Item -LiteralPath $lightingCandidate -Destination (Join-Path $lightingAddon 'maps/trento_povo_campus.vpk') -Force
Set-Content -LiteralPath (Join-Path $lightingAddon 'addoninfo.txt') -Encoding ascii -Value '"AddonInfo" { "IsTemplate" "0" "IsPlayable" "1" }'
$lightingExe = Join-Path $lightingInstall 'game/bin/win64/cs2.exe'
$lightingArguments = @('-steam','-retail','-addon','trento_povo_lighting_review','-tools','-insecure','-condebug','-vconsole','-netconport','27400','+game_type','0','+game_mode','2','+map','maps/trento_povo_campus.vpk','+bot_quota','0','+mp_warmup_pausetimer','1')
Start-Process -FilePath $lightingExe -WorkingDirectory (Split-Path -Parent $lightingExe) -ArgumentList $lightingArguments -WindowStyle Hidden
