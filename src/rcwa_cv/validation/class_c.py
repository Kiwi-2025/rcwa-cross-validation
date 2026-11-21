"""Check the representative two-dimensional benchmark at modest Fourier orders."""
from dataclasses import replace

from ..case_loader import resolve
from ..models import SolverSettings
from ..reporting.benchmark import read_sample
from .compare import differences, meets
from .study import POWER_KEYS, REFINE_MAGNITUDE, REFINE_PHASE, capture


GRIDS = {"C01": 480, "C02": 480, "C03": 480, "C04": 768, "C05": 448, "C06": 768}
ORDERS = (5, 7, 9, 11, 13, 15)


def verify(sample_at, settings, axes):
    sample = sample_at(settings)
    physics = max(sample["physics"].values())
    refinements = []
    for axis, values in axes.items():
        samples = [sample_at(replace(settings, **{axis: value})) for value in values]
        physics = max(physics, max(max(entry["physics"].values()) for entry in samples))
        for coarse, fine in zip(samples, samples[1:]):
            delta = differences(read_sample(coarse), read_sample(fine))
            refinements.append({"axis": axis, "coarse_settings": coarse["settings"],
                                "fine_settings": fine["settings"], **delta})
    return {
        "sample": sample, "refinements": refinements, "max_physics_error": physics,
        "power_converged": physics <= 1e-6 and all(
            step["complete"] and max(step[key] for key in POWER_KEYS) <= REFINE_MAGNITUDE for step in refinements
        ),
        "full_converged": physics <= 1e-6 and all(
            meets(step, REFINE_MAGNITUDE, REFINE_PHASE) for step in refinements
        ),
    }


def plan(case_id):
    first = {"C03": 2, "C06": 1}.get(case_id, 0)
    return {"orders": list(ORDERS[first:]), "grid": GRIDS[case_id], "separate_axes": case_id == "C06"}


def evaluate(spec, variant, point, solver, policy):
    samples = {}

    def measured(settings):
        if settings not in samples:
            case = resolve(spec, variant, point, settings)
            _, samples[settings] = capture(case, settings, solver)
        return samples[settings]

    orders, grid = policy["orders"], policy["grid"]
    for lower, center, upper in zip(orders, orders[1:], orders[2:]):
        separate_axes = policy["separate_axes"]
        settings = SolverSettings(center, grid, 1, center if separate_axes else None)
        axes = {"order": (lower, center, upper)}
        if separate_axes:
            axes["order_y"] = axes["order"]
        axes["grid"] = (grid, 2 * grid)
        result = verify(measured, settings, axes)
        if result["full_converged"]:
            break
    return result
