$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
$vitePath = Join-Path $projectRoot 'apps/web/node_modules/vite/bin/vite.js'
if (!(Test-Path $pythonPath) -or !(Test-Path $vitePath)) {
    throw 'Install the dependencies using README.md before starting Nexus.'
}
if (Test-Path (Join-Path $projectRoot '.local/database.json')) {
    & $pythonPath (Join-Path $projectRoot 'scripts/setup-postgres.py')
    if ($LASTEXITCODE) { throw 'Nexus PostgreSQL could not start.' }
} elseif (!$env:NEXUS_DATABASE_URL) {
    Write-Warning 'PostgreSQL is not configured. Nexus will start in read-only fixture mode.'
}
foreach ($port in @(8000, 5173)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. Close the earlier server or use the running Nexus session."
    }
}
$logDirectory = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Force $logDirectory | Out-Null
$apiProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'api.log') -RedirectStandardError (Join-Path $logDirectory 'api-error.log')
try {
    $webProcess = Start-Process -FilePath (Get-Command node).Source -ArgumentList ('"' + $vitePath + '"'), '--host', '127.0.0.1' -WorkingDirectory (Join-Path $projectRoot 'apps/web') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'web.log') -RedirectStandardError (Join-Path $logDirectory 'web-error.log')
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $null = Invoke-WebRequest 'http://127.0.0.1:8000/api/investigation' -TimeoutSec 1
            $null = Invoke-WebRequest 'http://127.0.0.1:5173' -TimeoutSec 1
            $ready = $true
            break
        } catch { Start-Sleep -Milliseconds 250 }
    }
    if (!$ready) { throw 'Startup failed. Inspect the logs in .local.' }
    Write-Output 'Nexus is running at http://127.0.0.1:5173'
    Write-Output "To stop this session: Stop-Process -Id $($apiProcess.Id),$($webProcess.Id)"
} catch {
    if ($webProcess -and !$webProcess.HasExited) { $webProcess.Kill() }
    if (!$apiProcess.HasExited) { $apiProcess.Kill() }
    throw
}
