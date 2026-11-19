from pathlib import Path

import numpy as np
import yaml

from .models import CaseSpec, Layer, Shape


ROOT = Path(__file__).resolve().parents[2]


def catalog(selector="all"):
    paths = sorted((ROOT / "cases").glob("*/*/case.yaml"))
    selector = selector.strip("/").upper()
    selected = [path for path in paths if selector in {
        "ALL", path.parent.name, path.parent.parent.name,
        f"{path.parent.parent.name}/{path.parent.name}"}]
    if not selected:
        raise ValueError(f"Unknown case or category: {selector}")
    return selected


def load_case(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def epsilon(value):
    return complex(*value) if isinstance(value, list) else complex(value)


def points(case, profile):
    if len(case["scan"]) > 1:
        raise ValueError("Define one sweep axis per case.")
    if case["scan"]:
        key, scan = next(iter(case["scan"].items()))
        values = (scan["quick"] if profile in ("quick", "pilot") else
                  np.unique([*np.linspace(scan["start"], scan["stop"], scan["count"]), *scan.get("extra", [])]))
    else:
        key, values = "wavelength_nm", [case["wavelength_nm"]]
    for variant, overrides in {"nominal": {}, **case["variants"]}.items():
        for value in values:
            yield variant, {**overrides, key: float(value)}


def resolve(case, variant, overrides, settings):
    c = dict(case, **overrides)
    period = tuple(c["period_nm"])
    layers = []
    for spec in c["layers"]:
        shapes = spec["shapes"]
        subdivisions = settings.slices if any("bottom_width_nm" in s for s in shapes) else 1
        for i in range(subdivisions):
            local = []
            for s in shapes:
                kind = s["kind"]
                if kind == "sinusoid":
                    # Midpoint piecewise-constant approximation shared by every backend.
                    dx = period[0] / settings.grid
                    for j in range(settings.grid):
                        x = (j + .5) * dx - period[0] / 2
                        n = s["mean_index"] + s["index_modulation"] * np.cos(2 * np.pi * x / period[0])
                        local.append(Shape("rectangle", complex(n*n), (x, 0), dx, period[1]))
                    continue
                x, y = s.get("center_nm", [0, 0])
                if s.get("shift_scan"):
                    x += c.get("shift_nm", 0)
                if kind == "circle":
                    width = length = 2 * (c.get("radius_nm", s["radius_nm"]) if s.get("radius_scan") else s["radius_nm"])
                else:
                    width = s["width_nm"]
                    width += (s.get("bottom_width_nm", width) - width) * (i + .5) / subdivisions
                    length = s["length_nm"] or period[1]
                rotation = c.get("rotation_deg", 0) if s.get("rotation_scan") else 0
                local.append(Shape(kind, epsilon(s["epsilon"]), (x, y), width, length, rotation))
            layers.append(Layer(spec["thickness_nm"] / subdivisions, epsilon(spec["epsilon"]), tuple(local)))
    wavelength = period[0] / c["normalized_frequency"] if "normalized_frequency" in c else c["wavelength_nm"]
    return CaseSpec(c["id"], variant, c["periodic_dimensions"], period, c["epsilon_incident"], c["epsilon_exit"],
                    wavelength, c["theta_deg"], c["phi_deg"], tuple(layers))
