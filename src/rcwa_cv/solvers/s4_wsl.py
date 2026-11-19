from functools import lru_cache
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import numpy as np

from .base import Unavailable
from .s4_worker import S4_REVISION, encode
from ..conventions import result_from_amplitudes


def _prefix():
    return (["wsl.exe", "-d", os.getenv("RCWA_S4_DISTRIBUTION", "Ubuntu-24.04"), "--cd", "/", "--exec"]
            if sys.platform == "win32" else [])


@lru_cache
def _command():
    source = Path(__file__).resolve().parents[2]
    src = str(source)
    prefix = _prefix()
    if prefix:
        mapped = os.getenv("RCWA_S4_SRC")
        if mapped:
            src = mapped
        elif len(source.drive) == 2 and source.drive.endswith(":"):
            src = f"/mnt/{source.drive[0].lower()}/" + "/".join(source.parts[1:])
        else:
            src = subprocess.check_output([*prefix, "wslpath", "-a", src], text=True, timeout=45).strip()
    return [*prefix, "env", f"PYTHONPATH={src}", "OPENBLAS_NUM_THREADS=1",
            os.getenv("RCWA_S4_PYTHON", "/usr/bin/python3")]


@lru_cache
def probe():
    try:
        subprocess.run([*_command(), "-c", "import S4, numpy, rcwa_cv.solvers.s4_worker"], check=True,
                       capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        raise Unavailable(f"S4 probe failed. Check the WSL environment and setup script. {detail.strip()}") from exc
    return {"version": S4_REVISION, "device": "CPU (WSL)" if _prefix() else "CPU"}


def solve(case, settings):
    metadata = probe()
    start = perf_counter()
    proc = subprocess.run([*_command(), "-m", "rcwa_cv.solvers.s4_worker"], input=encode(case, settings),
                          capture_output=True, text=True, timeout=180)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    data = json.loads(proc.stdout)
    amplitude = np.array(data["real"]) + 1j*np.array(data["imag"])
    return result_from_amplitudes(case, np.array(data["orders"]), amplitude,
                                  dict(metadata, wall_seconds=perf_counter()-start))
