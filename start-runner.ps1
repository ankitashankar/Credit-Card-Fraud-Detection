$ErrorActionPreference = "Stop"

$runnerDirectory = "C:\actions-runner"
$runnerScript = Join-Path $runnerDirectory "run.cmd"
$runnerConfiguration = Join-Path $runnerDirectory ".runner"

if (-not (Test-Path $runnerConfiguration)) {
    throw "The GitHub Actions runner is not configured. Configure it from $runnerDirectory before starting it."
}

if (-not (Test-Path $runnerScript)) {
    throw "Runner start script not found: $runnerScript"
}

Write-Host "Starting the GitHub Actions runner. Keep this window open; press Ctrl+C to stop it."
Push-Location $runnerDirectory
try {
    & $runnerScript
    if ($LASTEXITCODE -ne 0) {
        throw "The runner exited with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
