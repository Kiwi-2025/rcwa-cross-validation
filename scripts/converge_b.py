"""Refine each class B solver independently and compare against Lumerical."""
from argparse import ArgumentParser
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, replace
from pathlib import Path
import re
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_limits

from rcwa_cv.case_loader import ROOT, catalog, load_case, points, resolve
from rcwa_cv.conventions import wavevectors
from rcwa_cv.models import SolverSettings
from rcwa_cv.reporting.benchmark import optical_data, read_sample, report_text
from rcwa_cv.reporting.tables import POWER_METRICS, markdown_table, pretty
from rcwa_cv.runner import configure, software_versions
from rcwa_cv.solvers import MODULES, adapter, lumerical
from rcwa_cv.storage import read_json, write_json
from rcwa_cv.validation.compare import differences, meets
from rcwa_cv.validation.physics import checks


MAGNITUDE = 2.5e-4
PHASE = 0.25


def refinement_plan(case_id):
    if case_id == "B06":
        return {"order": (4, 8, 12, 18, 27), "grid": (64, 128, 256, 512, 1024)}
    if case_id == "B04":
        orders = (8, 16, 24, 36, 54, 81, 108)
        return {"order": orders, "grid": (2560, 5120, 10240), "slices": (8, 16, 32, 64, 128)}
    orders = (8, 16, 24, 36, 54, 81, 120, 168, 224, 288)
    return {"order": orders, "grid": (1024, 2048, 4096, 8192, 16384)}


def power_converged(delta):
    return (delta.get("independent_native_mesh", True) and delta["complete"]
            and max(delta[key] for key in POWER_METRICS) <= MAGNITUDE)


def full_converged(delta, phase_tolerance=PHASE):
    return delta.get("independent_native_mesh", True) and meets(delta, MAGNITUDE, phase_tolerance)


def lumerical_mode(case_id):
    if case_id in ("B02", "B05"):
        return "2D Li factorization"
    return "2D staircase polygon" if case_id == "B04" else "3D single ky sector"


def lumerical_in_plane(case, settings, fdtd, *, use_li=True):
    """Put the periodic direction along native y for Lumerical's 2D Li rule."""
    if case.theta != 0 or case.phi != 0:
        raise ValueError("This coordinate transform is defined for normal incidence.")
    script = lumerical.build_script(case, settings, match_fourier_order=True)
    script = script.replace('set("simulation region","3D");', 'set("simulation region","2D X-normal");')
    script = re.sub(r'set\("(mesh cells )?([xy])( span)?"',
                    lambda m: f'set("{m[1] or ""}{"y" if m[2] == "x" else "x"}{m[3] or ""}"', script)
    inactive = ("max number ku", "max number kv", "k vectors domain", "angle phi", "mesh cells x")
    script = "\n".join(line for line in script.splitlines() if all(name not in line for name in inactive))
    options = [f'setnamed("RCWA","max number k vectors",{settings.order});',
               f'setnamed("RCWA","use li factorization",{int(use_li)});']
    fdtd.eval(script.replace('run("RCWA");', '\n'.join([*options, 'run("RCWA");']), 1))
    power, amplitudes, totals, modes, fields = [
        fdtd.getv(key) for key in ("power", "amplitudes", "totals", "modes", "fields")
    ]
    for dataset in (power, amplitudes, modes, fields):
        dataset["n"], dataset["m"] = dataset["m"], dataset["n"]
        if "kx" in dataset:
            dataset["kx"], dataset["ky"] = dataset["ky"], dataset["kx"]
    for side in "RT":
        power[f"{side}s_power"], power[f"{side}p_power"] = power[f"{side}p_power"], power[f"{side}s_power"]
        totals[f"{side}s"], totals[f"{side}p"] = totals[f"{side}p"], totals[f"{side}s"]
    # The coordinate permutation swaps s/p incidence and the Cartesian field
    # components. Negate both mapped columns for the native incident s sign.
    native_fields = dict(fields)
    for offset in "fb":
        for target, source in (("s", "p"), ("p", "s")):
            for original, rotated in (("x", "y"), ("y", "x")):
                fields[f"ek{original}_{offset}{target}"] = -native_fields[f"ek{rotated}_{offset}{source}"]
    return lumerical.normalize(case, power, amplitudes, totals, modes, fields,
                               {"numerical_mode": lumerical_mode(case.id)})


def lumerical_result(case, settings, fdtd, *, force_3d=False):
    if case.id in ("B02", "B05"):
        return lumerical_in_plane(case, settings, fdtd)
    # The grating is invariant in y. Use a bookkeeping period small enough for
    # circular truncation to retain precisely the coupled ky sector.
    px, py = case.period
    case = replace(case, period=(px, min(py, px / (4 * settings.order + 4))))
    polygon = case.id == "B04" and not force_3d
    model = replace(case, layers=tuple(replace(layer, shapes=()) for layer in case.layers)) if polygon else case
    script = lumerical.build_script(model, settings, match_fourier_order=True)
    if case.id == "B04" and not force_3d:
        h = case.thickness * .5e-9
        z = -h
        right = []
        for layer in case.layers:
            x = layer.shapes[0].width * .5e-9
            upper = z + layer.thickness * 1e-9
            right.extend([(x, z), (x, upper)])
            z = upper
        boundary = right + [(-x, z) for x, z in reversed(right)]
        vertices = ";".join(f"{x:.17g},{z:.17g}" for x, z in boundary)
        shape = f"""addpoly;
set("name","taper");
set("vertices",[{vertices}]);
set("z span",{2 * case.period[1] * 1e-9:.17g});
set("first axis","x");
set("rotation 1",90);
set("z",{h:.17g});
set("material","<Object defined dielectric>");
set("index",{case.layers[0].shapes[0].epsilon.real**.5:.17g});
"""
        script = script.replace("addrcwa;", shape + "addrcwa;", 1)
        script = script.replace('set("simulation region","3D");', 'set("simulation region","2D Y-normal");')
        inactive = ("max number ku", "max number kv", "k vectors domain", "angle phi", "mesh cells y")
        script = "\n".join(line for line in script.splitlines() if all(p not in line for p in inactive))
        options = [f'setnamed("RCWA","max number k vectors",{settings.order});',
                   'setnamed("RCWA","use li factorization",0);']
    else:
        options = ['setnamed("RCWA","k vectors domain","circular");',
                   f'setnamed("RCWA","max number k vectors",{2 * settings.order + 1});']
    nonzero_orders = np.array([(m, 0) for m in range(-settings.order, settings.order + 1) if m])
    needs_phase_shift = (wavevectors(case, nonzero_orders)[1] > 1e-10).any()
    if needs_phase_shift and not polygon:
        options.append('setnamed("RCWA","report index",1);')
        script += '\nprofile = getresult("RCWA","index"); sampled_x = profile.x;'
    script = script.replace('run("RCWA");', '\n'.join([*options, 'run("RCWA");']), 1)
    fdtd.eval(script)
    datasets = [fdtd.getv(key) for key in ("power", "amplitudes", "totals", "modes", "fields")]
    mode = lumerical_mode(case.id) if polygon else "3D single ky sector"
    result = lumerical.normalize(case, *datasets, {"numerical_mode": mode})
    if not needs_phase_shift:
        return result
    if polygon:
        samples = settings.grid
    else:
        x = np.asarray(fdtd.getv("sampled_x")).ravel()
        if len(x) < 2 or not np.allclose(np.diff(x), case.period[0] * 1e-9 / len(x), rtol=1e-6, atol=0):
            raise ValueError("Phase alignment requires a uniform native x mesh.")
        samples = len(x)
    result.metadata["phase_mesh_samples"] = samples
    result.amplitude *= np.exp(-1j * np.pi * result.orders[:, 0] / samples)[None, :, None, None]
    if polygon:
        lookup = {m: i for i, (m, n) in enumerate(result.orders) if n == 0}
        for m in range(1, settings.order + 1):
            pos, neg = lookup[m], lookup[-m]
            symmetric = np.diagonal(result.amplitude[:, pos] * result.amplitude[:, neg].conj(), axis1=1, axis2=2)
            strong = (result.propagating[:, pos] & result.propagating[:, neg])[:, None] & (abs(symmetric) > 1e-6)
            if (abs(symmetric.imag[strong]) > 1e-7 * abs(symmetric[strong])).any():
                raise ValueError("B04 phases are inconsistent with the requested uniform x mesh.")
    return result


def solve_point(backend, spec, variant, point, settings, fdtd):
    case = resolve(spec, variant, point, settings)
    start = perf_counter()
    result = backend.solve(case, settings) if fdtd is None else lumerical_result(case, settings, fdtd)
    native = np.asarray(result.metadata.get("native_orders", result.orders))
    expected = {(m, 0) for m in range(-settings.order, settings.order + 1)}
    if {tuple(order) for order in native} != expected:
        raise ValueError(f"Unexpected Fourier basis at {settings}: {len(native)} orders.")
    physics = checks(result, case.lossy)
    if (not all(np.isfinite(v) for v in physics.values())
            or any(not np.isfinite(v).all() for v in (result.totals, result.power, result.amplitude))):
        raise ValueError("Non-finite simulation result.")
    return {
        "settings": asdict(settings), "fourier_bounds": [settings.order, 0], "wall_seconds": perf_counter() - start,
        "numerical_mode": result.metadata.get("numerical_mode", "native"),
        "phase_mesh_samples": result.metadata.get("phase_mesh_samples"), "physics": physics,
        **optical_data(result),
    }


def refine(backend, spec, variant, point, plan, fdtd, *, upper_axes=(), starting_values=None,
           phase_tolerance=PHASE):
    samples = {}

    def sample(settings):
        if settings not in samples:
            entry = solve_point(backend, spec, variant, point, settings, fdtd)
            samples[settings] = entry, read_sample(entry)
        return samples[settings]

    indices = dict.fromkeys(plan, 1)
    for axis in upper_axes:
        indices[axis] = len(plan[axis]) - 1
    for axis, value in (starting_values or {}).items():
        indices[axis] = plan[axis].index(value)
    while True:
        fine = SolverSettings(**{"slices": 1} | {axis: values[indices[axis]] for axis, values in plan.items()})
        primary, field = sample(fine)
        checks_by_axis = []
        advance = []
        for axis, values in plan.items():
            previous = replace(fine, **{axis: values[indices[axis] - 1]})
            coarse, coarse_field = sample(previous)
            check = differences(coarse_field, field)
            old_grid, new_grid = coarse["phase_mesh_samples"], primary["phase_mesh_samples"]
            independent = (old_grid is None or new_grid is None
                           or (old_grid != new_grid if axis == "grid" else old_grid == new_grid))
            check["independent_native_mesh"] = independent
            checks_by_axis.append({"axis": axis, "coarse_settings": asdict(previous),
                                   "coarse_native_grid": old_grid, **check})
            if not independent and indices["grid"] + 1 < len(plan["grid"]):
                advance.append((True, float("inf"), "grid"))
            elif not full_converged(check, phase_tolerance) and indices[axis] + 1 < len(values):
                advance.append((not check["complete"], max(
                    (check["max_phase_deg"] or 0) / phase_tolerance,
                    max(check[key] for key in (*POWER_METRICS, "max_amplitude")) / MAGNITUDE),
                    axis))
        if not advance:
            break
        indices[max(advance)[-1]] += 1
    valid = max(primary["physics"].values()) <= 1e-6
    return {
        "sample": primary, "refinements": checks_by_axis,
        "power_converged": valid and all(power_converged(check) for check in checks_by_axis),
        "full_converged": valid and all(full_converged(check, phase_tolerance) for check in checks_by_axis),
        "solves": len(samples),
    }


@contextmanager
def lumerical_resources():
    with lumerical.session() as fdtd:
        fdtd.eval('saved_rcwa_mode = getresource("RCWA","run within design environment");')
        fdtd.eval('setresource("RCWA","run within design environment",1);')
        try:
            yield fdtd
        finally:
            fdtd.eval('setresource("RCWA","run within design environment",saved_rcwa_mode);')


def run_cases(cache, solver, selected, point_indices=None):
    configure()
    backend = adapter(solver)
    with threadpool_limits(limits=4, user_api="blas"), (
        lumerical_resources() if solver == "lumerical" else nullcontext()
    ) as fdtd:
        software = backend.probe()
        if fdtd is not None:
            software["build"] = fdtd.version()
        print(solver, software, flush=True)
        paths = [catalog(case_id)[0] for case_id in selected] if selected else catalog("B")
        for path in paths:
            spec = load_case(path)
            case_id = spec["id"]
            plan = refinement_plan(case_id)
            upper_axes = ()
            if case_id == "B04" and solver != "meent":
                upper_axes = ("order", "slices")
            elif case_id == "B05" and solver in ("grcwa", "torcwa"):
                upper_axes = ("order", "grid")
            for i, (variant, point) in enumerate(points(spec, "quick")):
                if point_indices is not None and i not in point_indices:
                    continue
                record = cache / solver / case_id / f"{i:02d}.json"
                starts = {"order": 288, "grid": 4096} if (
                    solver == "lumerical" and case_id == "B01" and i in (0, 2)
                ) else None
                if record.is_file():
                    saved = read_json(record)
                    same_mode = saved["sample"].get("numerical_mode") == lumerical_mode(case_id)
                    uses_verified_grid = starts is None or saved["sample"]["settings"]["grid"] >= starts["grid"]
                    if solver != "lumerical" or (same_mode and uses_verified_grid):
                        continue
                print(solver, case_id, i, "refining", flush=True)
                initial = () if case_id == "B04" and solver == "lumerical" and i == 3 else upper_axes
                complete = refine(backend, spec, variant, point, plan, fdtd,
                                  upper_axes=initial, starting_values=starts)
                complete.update(point=point, variant=variant, software=software)
                write_json(record, complete)
                print(solver, case_id, i, complete["sample"]["settings"],
                      "full" if complete["full_converged"] else
                      "power" if complete["power_converged"] else "limit", flush=True)


def comparisons(left, reference):
    counts = dict(power_points=0, full_points=0, power_pass=0, full_pass=0)
    power = []
    full = []
    for candidate, base in zip(left, reference, strict=True):
        delta = differences(read_sample(candidate["sample"]), read_sample(base["sample"]))
        magnitude = max(delta[key] for key in POWER_METRICS)
        if candidate["power_converged"] and base["power_converged"] and delta["complete"]:
            counts["power_points"] += 1
            counts["power_pass"] += magnitude <= 1e-3
            power.append(magnitude)
        if candidate["full_converged"] and base["full_converged"] and delta["complete"]:
            counts["full_points"] += 1
            counts["full_pass"] += meets(delta, 1e-3)
            full.append(delta)
    return counts | {
        "max_power": max(power, default=None),
        "max_amplitude": max((d["max_amplitude"] for d in full), default=None),
        "max_phase_deg": max((d["max_phase_deg"] for d in full if d["max_phase_deg"] is not None), default=None),
    }


def refine_b03_phase(spec, solvers):
    # The weak zero-order cross-polarized reflection at 920 nm merits a
    # narrower phase convergence check than the study-wide threshold.
    i = next(i for i, entry in enumerate(solvers["meent"]) if entry["point"]["wavelength_nm"] == 920)
    original = solvers["meent"][i]
    reference = read_sample(solvers["lumerical"][i]["sample"])
    before = differences(read_sample(original["sample"]), reference)["max_phase_deg"]
    threshold = 0.05
    with threadpool_limits(limits=4, user_api="blas"):
        refined = refine(adapter("meent"), spec, original["variant"], original["point"],
                         refinement_plan("B03"), None, phase_tolerance=threshold)
    if not refined["full_converged"]:
        raise RuntimeError("The tighter B03 phase check did not satisfy the refinement criteria.")
    refined.update(point=original["point"], variant=original["variant"], software=original["software"])
    solvers["meent"][i] = refined
    return {
        "point": original["point"], "phase_tolerance_deg": threshold,
        "before_settings": original["sample"]["settings"], "before_reference_phase_deg": before,
        "after_settings": refined["sample"]["settings"],
        "after_reference_phase_deg": differences(read_sample(refined["sample"]), reference)["max_phase_deg"],
    }


def coverage_figure(records):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    solvers = tuple(MODULES)
    figure = Figure(figsize=(9.5, 4.2), layout="constrained")
    FigureCanvasAgg(figure)
    for axis, field, title in zip(figure.subplots(1, 2),
                                 ("power_converged", "full_converged"),
                                 ("Power convergence", "Power, amplitude and phase convergence"), strict=True):
        coverage = [[sum(s[field] for s in r["solvers"][name]) for name in solvers] for r in records]
        totals = np.asarray([len(r["solvers"]["lumerical"]) for r in records])
        ratio = np.asarray(coverage) / totals[:, None]
        axis.imshow(ratio, vmin=0, vmax=1, cmap="GnBu", aspect="auto")
        axis.set(xticks=range(len(solvers)), xticklabels=solvers, yticks=range(len(records)),
                 yticklabels=[r["case"] for r in records], title=title)
        for j, row in enumerate(coverage):
            for i, count in enumerate(row):
                axis.text(i, j, f"{count}/{totals[j]}", ha="center", va="center",
                          color="white" if ratio[j, i] > .7 else "#102d3b")
    target = ROOT / "results/figures/B-convergence.png"
    figure.savefig(target, dpi=160)


def publish(cache):
    records = []
    rows = []
    phase_check = None
    for path in catalog("B"):
        spec = load_case(path)
        case_id = spec["id"]
        count = len(list(points(spec, "quick")))
        solvers = {name: [read_json(cache / name / case_id / f"{i:02d}.json") for i in range(count)]
                   for name in MODULES}
        expected_points = list(points(spec, "quick"))
        for name, samples in solvers.items():
            for sample, (variant, point) in zip(samples, expected_points, strict=True):
                if sample["variant"] != variant or sample["point"] != point:
                    raise ValueError(f"Cached excitation differs from the current {case_id} case.")
                if name == "lumerical" and sample["sample"]["numerical_mode"] != lumerical_mode(case_id):
                    raise ValueError(f"Rerun Lumerical for {case_id} to use the validated numerical mode.")
        if case_id == "B03":
            phase_check = refine_b03_phase(spec, solvers)
        paired = {name: comparisons(solvers[name], solvers["lumerical"]) for name in MODULES if name != "lumerical"}
        records.append({"case": case_id, "solvers": solvers, "comparisons": paired})
        for name, values in paired.items():
            rows.append((case_id, name, f"{values['power_points']}/{count}", f"{values['full_points']}/{count}",
                         pretty(values["max_power"]), pretty(values["max_amplitude"]),
                         pretty(values["max_phase_deg"]), values["power_pass"], values["full_pass"]))
    destination = ROOT / "results" / "benchmark.json"
    dataset = read_json(destination)
    dataset["b_convergence"] = {
        "point_scope": "All published quick excitations for B01–B06",
        "refinement_magnitude": MAGNITUDE, "refinement_phase_deg": PHASE,
        "b03_meent_phase_check": phase_check,
        "lumerical_phase_alignment": "exp(-i pi m/Nx) for B01, B03, B04 and B06 using the reported uniform native mesh",
        "software": software_versions(), "cases": records,
    }
    write_json(destination, dataset)
    coverage_figure(records)
    eligible = sum(pair["full_points"] for record in records for pair in record["comparisons"].values())
    passed = sum(pair["full_pass"] for record in records for pair in record["comparisons"].values())
    total = sum(len(record["solvers"]["lumerical"]) * len(record["comparisons"]) for record in records)
    complete = [record["case"] for record in records if all(
        pair["full_pass"] == len(record["solvers"]["lumerical"]) for pair in record["comparisons"].values())]
    tables = [
        "# Class B convergence benchmark",
        f"Each solver is refined independently at all {total // (len(MODULES) - 1)} published class B excitations. "
        "Lumerical is the comparison reference. Maxima below use only points with the corresponding "
        "convergence evidence in both solvers. A dash denotes unavailable paired evidence.",
        "![Coverage of the individual convergence checks](results/figures/B-convergence.png)",
        "## Comparisons against Lumerical",
        markdown_table(("Case", "Solver", "Power pairs", "Full pairs", "Max Δpower", "Max |Δamplitude|",
                        "Max Δphase (deg)", "Power passes", "Full passes"), rows),
    ]
    settings_rows = []
    for record in records:
        for name, samples in record["solvers"].items():
            axes = ("order", "grid", "slices") if record["case"] == "B04" else ("order", "grid")
            ranges = [sorted({s["sample"]["settings"][axis] for s in samples}) for axis in axes]
            failed = [a for s in samples for a in s["refinements"] if not full_converged(a)]
            limits = sorted({a["axis"] for a in failed})
            change = max((a["max_amplitude"] for a in failed), default=None)
            settings_rows.append((record["case"], name, samples[0]["sample"].get("numerical_mode", "native"),
                                  sum(s["power_converged"] for s in samples),
                                  sum(s["full_converged"] for s in samples),
                                  " / ".join(", ".join(map(str, values)) for values in ranges),
                                  ", ".join(limits) or "—", pretty(change)))
    versions = {name: samples[0]["software"] for name, samples in records[0]["solvers"].items()}
    version_rows = [(name, info["version"], info.get("gpu", info["device"]),
                     info.get("build") or info.get("torch", "—")) for name, info in versions.items()]
    tables += [
        "## Settings and unresolved axes",
        markdown_table(("Case", "Solver", "Mode", "Power converged", "Fully converged",
                        "Order / grid / slices", "Unresolved axes", "Largest unresolved amplitude change"),
                       settings_rows),
        "## Software",
        markdown_table(("Solver", "Version", "Device", "Lumerical build or PyTorch version"), version_rows),
        "## Method",
        "Each active axis is checked against its preceding setting while all other axes are fixed. "
        "The absolute refinement tolerance is 2.5e-4 for power and complex amplitude, and 0.25° for "
        "eligible phase channels. The comparison tolerances are 1e-3 and 0.5°. Lumerical's actual native "
        "order lists are checked. Lumerical uses native 2D Li factorization for B02 and B05 in "
        "permuted transverse coordinates. In controls at 1200 nm and M = 16 and 36, the rotated model "
        "with Li disabled agreed with the direct 3D model within 7.7e-12 in complex amplitude. "
        "B04 uses the direct 2D numerical mode with a polygon that preserves the staircase geometry of "
        "each slice setting. At 620 nm this representation matched grcwa within 2.8e-13 in complex "
        "amplitude in controls with 16 and 32 slices. B01, B03, and B06 use the 3D solver "
        "with one coupled y sector. "
        "For propagating nonzero orders the field phase is aligned using the native mesh spacing and "
        "the predicted half-sample shift. The spacing is verified from the reported x mesh or, for the "
        "mirror-symmetric B04 polygon, from the phase relation of opposite orders. Powers are preserved. "
        "The original quick benchmark keeps its published settings. "
        "[Ansys RCWA solver and Li factorization](https://optics.ansys.com/hc/en-us/articles/12959229278611-RCWA-Solver-Simulation-Object)",
        "```powershell\n& .\\.venv\\Scripts\\python.exe scripts\\converge_b.py\n```",
        "The script resumes from completed point records in `.runs/b-convergence`. Pass `--cache` with "
        "a different directory to run from scratch.",
        "[Numerical dataset](results/benchmark.json) · [Reproduction script](scripts/converge_b.py) · "
        "[B06 phase diagnosis](PERIODIC_DIAGNOSIS.md#b06)",
        f"The B03 Meent point at 920 nm received an additional independent phase refinement to 0.05°. "
        f"The maximum cross-solver phase change at that point went from "
        f"{phase_check['before_reference_phase_deg']:.3f}° to {phase_check['after_reference_phase_deg']:.3f}°. "
        "The table uses the finer result.",
        "## Conclusion",
        f"Both solvers satisfy the complete refinement criteria in {eligible} of {total} possible "
        f"open-source/Lumerical point comparisons. {passed} of those comparisons meet the agreement "
        f"tolerances. Cases with all points and all three comparisons passing are {', '.join(complete) or 'none'}. "
        "The unresolved axes identify which settings still limit the other comparisons.",
    ]
    (ROOT / "B_CONVERGENCE.md").write_text("\n\n".join(tables) + "\n", encoding="utf-8", newline="\n")
    figures = {case["case"]: sorted((ROOT / "results/figures" / case["case"]).glob("*.png"))
               for case in dataset["cases"]}
    (ROOT / "BENCHMARK_REPORT.md").write_text(report_text(dataset, figures), encoding="utf-8", newline="\n")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--solver", choices=MODULES)
    parser.add_argument("--case", nargs="+", choices=[f"B{i:02d}" for i in range(1, 7)])
    parser.add_argument("--point", type=int, nargs="+", help="Zero-based quick point indices.")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--cache", type=Path, default=ROOT / ".runs" / "b-convergence")
    args = parser.parse_args()
    if args.publish:
        publish(args.cache)
        return
    for solver in [args.solver] if args.solver else MODULES:
        run_cases(args.cache, solver, args.case, args.point)
    if not args.solver and not args.case and args.point is None:
        publish(args.cache)


if __name__ == "__main__":
    main()
