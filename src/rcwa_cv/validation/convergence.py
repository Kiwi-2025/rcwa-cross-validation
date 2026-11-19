from dataclasses import replace

from .compare import differences, meets


def settings_series(case, profile, name):
    dim = case["periodic_dimensions"]
    if name == "reference" or dim == 0:
        from ..models import SolverSettings
        return [("base", SolverSettings(0, 2, 1))]
    from ..models import SolverSettings
    axis = "2d" if dim == 2 else "1d"
    modes, grid = profile[f"orders_{axis}"], profile[f"grid_{axis}"]
    slices = profile["slices"] if case["id"] == "B04" else [1]
    base = SolverSettings(modes[-1], grid[-1], slices[-1])
    axes = {"order": modes, "grid": grid, "slices": slices}
    if name == "s4" and case["id"] != "B06":
        axes.pop("grid")
    return [("base", base), *((key, replace(base, **{key: value}))
                              for key, values in axes.items() for value in values[:-1])]


def check_axis(samples, base):
    return [{"axis": label, "differences": differences(result, base)} for label, result in samples]


def converged(samples):
    latest = {entry["axis"]: entry["differences"] for entry in samples}
    return all(meets(values, 2.5e-4, .25) for values in latest.values())
