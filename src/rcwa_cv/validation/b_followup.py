"""Verify the unresolved one-dimensional grating cases at finer settings."""
from argparse import ArgumentParser
from contextlib import nullcontext
from dataclasses import asdict, replace
from pathlib import Path

from threadpoolctl import threadpool_limits

from ..case_loader import ROOT, catalog, load_case, points
from ..models import SolverSettings
from ..reporting.benchmark import DATASET, refresh_published_report
from ..runner import configure
from ..solvers import MODULES, adapter
from ..storage import read_json, write_json
from .class_b import full_converged, lumerical_resources, power_converged, refinement_difference, solve_point
from .study import cache_case, version_signature


CACHE = ROOT / ".runs" / "b-followup"
CASES = ("B02", "B04", "B05")
LI_MODE = "1D Li inverse rule"
NATIVE_PROBE = {"B02": ("grcwa", 4096), "B05": ("torcwa", 16384)}


def plan(case_id, point_index, solver=None):
    if case_id == "B04":
        order = 128 if solver == "meent" else 148
        return (SolverSettings(order, 5120, 128),
                {"order": (108, 128, 148), "grid": (2560, 5120),
                 "slices": (96, 128, 192) if point_index == 0 else (64, 128)})
    order = 96 if case_id == "B05" else 72
    return (SolverSettings(order, 2048, 1),
            {"order": (54, 72, 96) if case_id == "B05" else (36, 54, 72), "grid": (512, 1024, 2048)})


def certify(sample_at, settings, levels):
    final = sample_at(settings)
    refinements = []
    valid = max(final["physics"].values()) <= 1e-6
    for axis, values in levels.items():
        series = [sample_at(replace(settings, **{axis: value})) for value in values]
        valid = valid and all(max(sample["physics"].values()) <= 1e-6 for sample in series)
        refinements.extend(refinement_difference(axis, a, b) for a, b in zip(series, series[1:]))
    return {"sample": final, "refinements": refinements,
            "power_converged": valid and all(power_converged(check) for check in refinements),
            "full_converged": valid and all(full_converged(check) for check in refinements)}


def run(solver, selected, indices, cache):
    configure()
    backend = adapter(solver)
    with threadpool_limits(limits=5, user_api="blas"), (
        lumerical_resources() if solver == "lumerical" else nullcontext()
    ) as fdtd:
        software = backend.probe()
        if fdtd is not None:
            software["build"] = fdtd.version()
        for case_id in selected:
            spec = load_case(catalog(case_id)[0])
            cache_case(cache, spec)
            li = case_id in ("B02", "B05") and solver in ("grcwa", "torcwa")
            for i, (variant, point) in enumerate(points(spec, "quick")):
                if indices is not None and i not in indices:
                    continue
                if case_id == "B04" and (i == 3 or (solver == "meent" and i != 0)):
                    continue
                path = cache / "samples" / solver / case_id / f"{i:02d}"
                settings, levels = plan(case_id, i, solver)
                destination = cache / "verified" / solver / case_id / f"{i:02d}.json"
                study = {"settings": asdict(settings), "levels": {key: list(values) for key, values in levels.items()},
                         "software": software, "variant": variant, "point": point}
                probe = NATIVE_PROBE.get(case_id)
                needs_probe = i == 0 and probe is not None and probe[0] == solver
                if destination.is_file():
                    saved = read_json(destination)
                    if (saved["followup_plan"] == study
                            and (not needs_probe or "native_order_probe" in saved)):
                        continue
                provenance = path / "software.json"
                if provenance.is_file() and read_json(provenance) != software:
                    raise ValueError(f"The recorded software differs for {case_id}. Use a new follow-up cache.")
                write_json(provenance, software)

                def sample_at(setting, *, use_li=li):
                    suffix = "-li" if use_li else ""
                    sample_path = path / f"{setting.order}-{setting.grid}-{setting.slices}{suffix}.json"
                    if sample_path.is_file():
                        sample = read_json(sample_path)
                        if SolverSettings(**sample["settings"]) != setting or (
                            use_li and sample["numerical_mode"] != LI_MODE
                        ):
                            raise ValueError(f"Unexpected cached settings at {sample_path}.")
                        return sample
                    print(solver, case_id, i, setting, flush=True)
                    sample = solve_point(backend, spec, variant, point, setting, fdtd, li=use_li)
                    write_json(sample_path, sample)
                    return sample

                print(solver, case_id, i, "checking", flush=True)
                result = certify(sample_at, settings, levels)
                if case_id == "B04" and i == 0 and solver != "meent":
                    result["coarse_slice_probe"] = refinement_difference(
                        "slices", sample_at(replace(settings, slices=64)), result["sample"]
                    )
                if needs_probe:
                    orders = [sample_at(SolverSettings(m, probe[1], 1), use_li=False) for m in (288, 384, 512)]
                    result["native_order_probe"] = [refinement_difference("order", a, b)
                                                    for a, b in zip(orders, orders[1:])]
                write_json(destination, result | {"variant": variant, "point": point, "software": software,
                                                    "followup_plan": study})
                print(solver, case_id, i, "full" if result["full_converged"] else
                      "power" if result["power_converged"] else "limit", flush=True)


def apply(data, cache, selected):
    for record in data["cases"]:
        case_id = record["case"]
        if case_id not in selected:
            continue
        if read_json(cache / "case-definitions" / f"{case_id}.json") != record["case_definition"]:
            raise ValueError(f"The cached definition of {case_id} differs from the benchmark.")
        for solver, entries in record["solvers"].items():
            for i, old in enumerate(entries):
                path = cache / "verified" / solver / case_id / f"{i:02d}.json"
                if not path.is_file():
                    continue
                row = read_json(path)
                if ((row["variant"], row["point"]) != (old["variant"], old["point"])
                        or version_signature(row["software"]) != version_signature(old["software"])):
                    raise ValueError(f"Cached {solver} result differs from {case_id} point {i}.")
                if row["sample"]["numerical_mode"] == LI_MODE:
                    native = record.setdefault("native_solvers", {})
                    native.setdefault(solver, entries.copy())
                entries[i] = row


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, nargs="+", default=CASES)
    parser.add_argument("--solver", choices=MODULES)
    parser.add_argument("--point", type=int, nargs="+")
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.publish:
        data = read_json(DATASET)
        apply(data, args.cache, args.case)
        refresh_published_report(data)
    else:
        for solver in [args.solver] if args.solver else MODULES:
            run(solver, args.case, args.point, args.cache)


if __name__ == "__main__":
    main()
