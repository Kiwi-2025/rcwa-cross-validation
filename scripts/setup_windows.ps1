$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    uv sync --locked --extra cuda
    if ($LASTEXITCODE -ne 0) { throw 'The Python environment could not be installed.' }
    uv run --no-sync rcwa-cv doctor
} finally {
    Pop-Location
}
