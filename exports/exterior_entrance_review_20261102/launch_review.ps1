$ErrorActionPreference = 'Stop'
$reviewRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$reviewPython = Join-Path $reviewRoot '.venv/Scripts/python.exe'
$reviewInstall = 'C:/Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive'
$reviewCandidate = Join-Path $reviewRoot 'build/exterior-entrance-20261102/candidate.vpk'
if (!(Test-Path -LiteralPath $reviewCandidate)) { throw 'Candidate package is not ready' }
& $reviewPython (Join-Path $reviewRoot 'tools/verify_cs2_package.py') $reviewCandidate --map trento_povo_campus --model povo1_campus --overview (Join-Path $reviewRoot 'exports/povo_campus/radar/trento_povo_campus.txt') --full-crc --report (Join-Path $PSScriptRoot 'candidate-package-check.json')
if ($LASTEXITCODE -ne 0) { throw 'Candidate verification failed' }
if (Get-Process cs2 -ErrorAction SilentlyContinue) {
    # Refuse to replace any session other than this project's solo review map.
    & $reviewPython -c "from tools.playtest_povo_survey import Console,Driver; c=Console(27400); Driver(c,'trento_povo_campus').guard(); c.send('quit'); c.close()"
    if ($LASTEXITCODE -ne 0) { throw 'Solo-session guard rejected restart' }
    for ($reviewWait=0; $reviewWait -lt 160; $reviewWait++) {
        if (!(Get-Process cs2 -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Milliseconds 250
    }
    if (Get-Process cs2 -ErrorAction SilentlyContinue) { throw 'Previous game did not exit' }
}
$reviewAddon = Join-Path $reviewInstall 'game/csgo_addons/trento_povo_entrance_review'
New-Item -ItemType Directory -Force -Path (Join-Path $reviewAddon 'maps') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $reviewInstall 'content/csgo_addons/trento_povo_entrance_review') | Out-Null
Copy-Item -LiteralPath $reviewCandidate -Destination (Join-Path $reviewAddon 'maps/trento_povo_campus.vpk') -Force
Set-Content -LiteralPath (Join-Path $reviewAddon 'addoninfo.txt') -Encoding ascii -Value '"AddonInfo" { "IsTemplate" "0" "IsPlayable" "1" }'
$reviewExe = Join-Path $reviewInstall 'game/bin/win64/cs2.exe'
$reviewArguments = @('-steam','-retail','-addon','trento_povo_entrance_review','-tools','-insecure','-condebug','-vconsole','-netconport','27400','+game_type','0','+game_mode','2','+map','maps/trento_povo_campus.vpk','+bot_quota','0','+mp_warmup_pausetimer','1')
Start-Process -FilePath $reviewExe -WorkingDirectory (Split-Path -Parent $reviewExe) -ArgumentList $reviewArguments -WindowStyle Hidden
