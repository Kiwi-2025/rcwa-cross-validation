import json
from pathlib import Path

import numpy as np

from .models import SimulationResult


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_result(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, orders=result.orders, propagating=result.propagating,
                        power=result.power, amplitude=result.amplitude, totals=result.totals)


def load_result(path):
    with np.load(path, allow_pickle=False) as f:
        return SimulationResult(**{k: f[k] for k in f.files}, metadata={})
