"""Run and publish the independently checked optical benchmark settings."""
from argparse import ArgumentParser
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_limits

from ..case_loader import ROOT, catalog, load_case, points, resolve
from ..models import SolverSettings
from ..geometry import rectangular_orders
from ..references import multilayer
from ..reporting.benchmark import DATASET, optical_data, refresh_published_report
from ..runner import configure, software_versions
from ..solvers import MODULES, adapter, lumerical
from ..storage import read_json, write_json
from .compare import differences, meets
from .physics import checks


CACHE = ROOT / ".runs" / "abc-convergence"
POWER_KEYS = ("max_R", "max_T", "max_A", "max_order_power")
REFINE_MAGNITUDE = 2.5e-4
REFINE_PHASE = 0.25


def version_signature(info):
    return tuple(info.get(key) for key in ("version", "build", "cuda", "torch"))


def cache_case(cache, spec):
    path = cache / "case-definitions" / f"{spec['id']}.json"
    if path.is_file():
        if read_json(path) != spec:
            raise ValueError(f"The definition of {spec['id']} changed. Rerun with a new --cache directory.")
    else:
        write_json(path, spec)


def study_solve(case, settings, solver, *, numerical_mode="native"):
    """Use the same numerical mode in the study and in notebook reruns."""
    if solver != "lumerical":
        if numerical_mode == "1D Li inverse rule":
            return adapter(solver).solve(case, settings, li_factorization=True)
        if numerical_mode in ("Exact shape Fourier coefficients", "Exact shape Fourier coefficients (direct operator)"):
            return adapter(solver).solve(case, settings, exact_shapes=True)
        return adapter(solver).solve(case, settings)
    if case.id.startswith("B"):
        from .class_b import lumerical_result
        with lumerical.session() as fdtd:
            result = lumerical_result(case, settings, fdtd)
            result.metadata.update(lumerical.probe(), build=fdtd.version())
            return result
    centered = numerical_mode == "3D rectangular CAD (centered x phase)"
    tangent = numerical_mode == "3D tangent vector field"
    result = lumerical.solve(case, settings, match_fourier_order=case.dimensions == 2,
                             centered_x=centered, tangent=tangent)
    if case.dimensions == 2:
        expected = set(map(tuple, rectangular_orders(case, settings)))
        if set(map(tuple, result.metadata["native_orders"])) != expected:
            raise ValueError(f"Unexpected Lumerical Fourier basis at {settings}.")
        result.metadata["numerical_mode"] = numerical_mode if centered or tangent else "3D rectangular CAD"
    return result


def capture(case, settings, solver, *, material_operator=None, numerical_mode="native"):
    start = perf_counter()
    result = (study_solve(case, settings, solver, numerical_mode=numerical_mode) if material_operator is None else
              adapter(solver).solve(case, settings, material_operator=material_operator))
    physics = checks(result, case.lossy)
    if any(not np.isfinite(value).all() for value in (result.amplitude, result.power, result.totals)):
        raise ValueError("Non-finite optical result.")
    if not all(np.isfinite(value) for value in physics.values()):
        raise ValueError("Non-finite physical check.")
    return result, {
        "settings": {key: value for key, value in asdict(settings).items() if value is not None},
        "numerical_mode": material_operator or result.metadata.get("numerical_mode", "native"),
        "fourier_bounds": np.abs(result.orders).max(axis=0).tolist(),
        "wall_seconds": perf_counter() - start,
        "physics": physics,
        **{key: result.metadata[key] for key in ("phase_mesh_x_count", "peak_allocated_bytes", "exterior_algebra")
           if key in result.metadata},
        **optical_data(result),
    }


def evaluate_planar(spec, variant, point, solver):
    settings = SolverSettings(0, 2, 1)
    case = resolve(spec, variant, point, settings)
    final, sample = capture(case, settings, solver)
    delta = differences(final, multilayer.solve(case, settings))
    valid = max(sample["physics"].values()) <= 1e-6
    return {
        "sample": sample,
        "refinements": [{"axis": "analytic", **delta}],
        "power_converged": valid and delta["complete"] and max(delta[key] for key in POWER_KEYS) <= 1e-8,
        "full_converged": valid and meets(delta, 1e-8),
    }


def run_ac(solver, group, cache=CACHE, selected=None, point_indices=None):
    from . import class_c

    configure()
    if group == "C":
        cache = cache / "class-c"
    context = lumerical.session() if solver == "lumerical" else nullcontext()
    with threadpool_limits(limits=3, user_api="blas"), context as fdtd:
        software = adapter(solver).probe()
        if fdtd is not None:
            software["build"] = fdtd.version()
        for path in catalog(group):
            spec = load_case(path)
            case_id = spec["id"]
            if selected and case_id not in selected:
                continue
            cache_case(cache, spec)
            policy = class_c.plan(case_id) if group == "C" else None
            for i, (variant, point) in enumerate(points(spec, "quick")):
                if point_indices is not None and i not in point_indices:
                    continue
                destination = cache / solver / case_id / f"{i:02}.json"
                identity = {"variant": variant, "point": point, "software": software}
                if policy is not None:
                    identity["plan"] = policy
                if destination.is_file():
                    saved = read_json(destination)
                    if "sample" in saved and all(saved.get(key) == value for key, value in identity.items()):
                        continue
                try:
                    if policy is None:
                        result = evaluate_planar(spec, variant, point, solver)
                    else:
                        result = class_c.evaluate(spec, variant, point, solver, policy)
                except Exception as exc:
                    result = {"error": f"{type(exc).__name__}: {exc}", "refinements": [],
                              "power_converged": False, "full_converged": False}
                write_json(destination, result | identity)
                status = "full" if result["full_converged"] else "power" if result["power_converged"] else "limit"
                settings = result.get("sample", {}).get("settings")
                print(solver, case_id, i, status, settings or result["error"], flush=True)


def saved_b_cases(data):
    if "b_convergence" in data:
        return {record["case"]: record for record in data["b_convergence"]["cases"]}
    return {record["case"]: record for record in data.get("cases", [])
            if record["case"].startswith("B") and "comparisons" in record}


def publish(cache=CACHE, b_cache=None):
    from .class_b import refine_b03_phase

    data = read_json(DATASET) if DATASET.exists() else {}
    published_b = saved_b_cases(data)
    cases = []
    for path in catalog():
        spec = load_case(path)
        case_id = spec["id"]
        canonical = list(points(spec, "quick"))
        if case_id in published_b and b_cache is None:
            previous = published_b[case_id]
            if previous.get("case_definition", spec) != spec:
                raise ValueError(f"The definition of {case_id} changed. Use benchmark --fresh-b.")
            solvers = previous["solvers"]
        else:
            source = b_cache if case_id.startswith("B") else cache / "class-c" if case_id.startswith("C") else cache
            if source is None:
                source = ROOT / ".runs" / "b-convergence"
            cache_case(source, spec)
            solvers = {name: [read_json(source / name / case_id / f"{i:02d}.json")
                              for i in range(len(canonical))] for name in MODULES}
            if case_id == "B03":
                refine_b03_phase(spec, solvers)
        for name, rows in solvers.items():
            for entry, (variant, point) in zip(rows, canonical, strict=True):
                if (entry["variant"], entry["point"]) != (variant, point):
                    raise ValueError(f"Cached {name} excitation differs from {case_id}.")
        record = {"case": case_id, "title": spec["title"], "case_definition": spec,
                  "points": [{"variant": variant, **point} for variant, point in canonical], "solvers": solvers}
        if case_id in published_b and b_cache is None and "native_solvers" in previous:
            record["native_solvers"] = previous["native_solvers"]
        cases.append(record)
    provenance = software_versions()
    for name in MODULES:
        versions = [entry["software"] for case in cases for entry in case["solvers"][name]]
        signatures = {version_signature(info) for info in versions}
        if len(signatures) != 1:
            raise ValueError(f"The recorded settings use mixed versions for {name}.")
        info = versions[0]
        provenance[name] = info["version"]
        if name == "lumerical":
            provenance["Lumerical build"] = info["build"]
        if name == "torcwa":
            provenance["torcwa CUDA runtime"] = info["cuda"]
            provenance["torcwa GPU"] = ", ".join(sorted({info["gpu"] for info in versions}))
    refresh_published_report({"profile": "convergence", "comparison_reference": "lumerical",
                              "point_index": "zero-based", "software": provenance, "cases": cases})


def run_benchmark(cache=CACHE, *, fresh_b=False):
    from .class_b import run_cases

    data = read_json(DATASET) if DATASET.exists() else {}
    published_b = saved_b_cases(data)
    for solver in MODULES:
        run_ac(solver, "A", cache)
        run_ac(solver, "C", cache)
    signatures = {
        solver: version_signature(read_json(cache / solver / "A01/00.json")["software"])
        for solver in MODULES
    }
    reuse_b = not fresh_b and all(
        (record := published_b.get(spec["id"])) is not None
        and record.get("case_definition", spec) == spec
        and all(version_signature(row["software"]) == signatures[solver]
                for solver, rows in record["solvers"].items() for row in rows)
        for spec in map(load_case, catalog("B"))
    )
    if not reuse_b:
        for solver in MODULES:
            run_cases(cache, solver, None)
    publish(cache, None if reuse_b else cache)
    if not reuse_b:
        from .b_followup import CASES, apply, run as followup

        followup_cache = cache / "b-followup"
        for solver in MODULES:
            followup(solver, CASES, None, followup_cache)
        refreshed = read_json(DATASET)
        apply(refreshed, followup_cache, CASES)
        refresh_published_report(refreshed)


def main(default_group=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("A", "B", "C"), default=default_group)
    parser.add_argument("--solver", choices=MODULES)
    parser.add_argument("--case", nargs="+")
    parser.add_argument("--point", type=int, nargs="+")
    parser.add_argument("--cache", type=Path, default=ROOT / ".runs" / "b-convergence" if default_group == "B" else CACHE)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.publish:
        publish(CACHE if args.group == "B" else args.cache, args.cache if args.group == "B" else None)
    elif not args.group:
        run_benchmark(args.cache)
    else:
        for solver in [args.solver] if args.solver else MODULES:
            if args.group == "B":
                from .class_b import run_cases
                run_cases(args.cache, solver, args.case, args.point)
            else:
                run_ac(solver, args.group, args.cache, args.case, args.point)


if __name__ == "__main__":
    main()
