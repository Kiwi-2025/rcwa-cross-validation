$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        uv venv --python 3.11
        if ($LASTEXITCODE -ne 0) { throw 'The virtual environment could not be created.' }
    }
    $python = '.venv\Scripts\python.exe'
    uv pip install --python $python --index-url https://download-r2.pytorch.org/whl/cu128 'torch==2.8.0+cu128'
    if ($LASTEXITCODE -ne 0) { throw 'CUDA PyTorch could not be installed.' }
    uv pip install --python $python -e '.[cuda,notebook,dev]'
    if ($LASTEXITCODE -ne 0) { throw 'The Python environment could not be installed.' }
    & $python -m rcwa_cv.cli doctor
} finally {
    Pop-Location
}
