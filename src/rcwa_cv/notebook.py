"""Reproduce the validated solver-specific settings shown in each case notebook."""
from contextlib import nullcontext

from threadpoolctl import threadpool_limits

from .case_loader import load_case, points, resolve
from .models import SolverSettings
from .reporting.benchmark import DATASET, case_table, compare_certified, solver_label
from .reporting.tables import BASELINE, comparison_tolerance, markdown_table
from .runner import configure
from .solvers import adapter, lumerical
from .storage import read_json
from .validation.study import study_solve, version_signature


def case_setup(case_path):
    configure()
    spec = load_case(case_path)
    data = read_json(DATASET)
    record = next(c for c in data["cases"] if c["case"] == spec["id"])
    current = [{"variant": variant, **point} for variant, point in points(spec, "quick")]
    if current != record["points"] or record.get("case_definition") != spec:
        raise ValueError("Rebuild the convergence benchmark for the current case before running the notebook.")
    return spec, record


def show_settings(record):
    from IPython.display import Markdown, display

    rows = []
    for name, samples in record["solvers"].items():
        for i, row in enumerate(samples):
            sample = row.get("sample", {})
            settings = sample.get("settings", {})
            order = settings.get("order", "—")
            if settings.get("order_y") is not None:
                order = f"{order}×{settings['order_y']}"
            status = ("Full" if row["full_converged"] else "Power only" if row["power_converged"] else
                      "Unverified")
            rows.append((name, i, ", ".join(f"{k}={v}" for k, v in record["points"][i].items()),
                         sample.get("numerical_mode", "native") if sample else "—",
                         order, settings.get("grid", "—"), settings.get("slices", "—"), status))
    display(Markdown(markdown_table(("Solver", "Point", "Excitation", "Mode", "Half-order", "Grid", "Slices",
                                    "Convergence evidence"), rows)))


def solve_sweep(solver, spec, record):
    """Rerun the final settings on points eligible for a paired comparison."""
    paired = record["comparisons"].values() if solver == BASELINE else [record["comparisons"][solver]]
    indices = sorted({row["point"] for comparison in paired for row in comparison})
    if not indices:
        return {}
    samples = record["solvers"][solver]
    if solver == BASELINE:
        from .validation.class_b import lumerical_resources
        session = lumerical_resources() if spec["id"].startswith("B") else lumerical.session()
    else:
        session = nullcontext()
    results = {}
    with threadpool_limits(limits=3, user_api="blas"), session as fdtd:
        software = adapter(solver).probe()
        if fdtd is not None:
            software["build"] = fdtd.version()
        for i in indices:
            row = samples[i]
            if version_signature(row["software"]) != version_signature(software):
                raise ValueError(f"Rebuild the benchmark settings for this {solver} version.")
            settings = SolverSettings(**row["sample"]["settings"])
            case = resolve(spec, row["variant"], row["point"], settings)
            mode = row["sample"].get("numerical_mode", "native")
            result = study_solve(case, settings, solver, numerical_mode=mode)
            actual_mode = result.metadata.get("numerical_mode", "native")
            if actual_mode != mode:
                raise ValueError(f"The recorded numerical mode for {solver} differs at point {i}.")
            results[i] = result
    return results


def show_results(record, results):
    from IPython.display import Markdown, display
    import matplotlib.pyplot as plt

    pairs = compare_certified(record, results)
    display(Markdown(case_table(pairs, len(record["points"]), record)))
    if not any(pairs.values()):
        message = ("No excitation has convergence evidence from all four solvers."
                   if record.get("joint_convergence") else "This case has no points with paired convergence evidence.")
        display(Markdown(message))
        return
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.4), layout="constrained")
    axes_spec = (("power", "Power difference", comparison_tolerance(record["case"])),
                 ("amplitude", "Complex-amplitude difference", comparison_tolerance(record["case"])),
                 ("phase_deg", "Phase difference (deg)", .5))
    for axis, (metric, title, limit) in zip(axes, axes_spec, strict=True):
        has_data = False
        for name, rows in pairs.items():
            values = [(row["point"], row[metric]) for row in rows if row.get(metric) is not None]
            if values:
                has_data = True
                x, y = zip(*values, strict=True)
                axis.scatter(x, [max(value, 1e-16) for value in y], label=solver_label(name, record))
        if has_data:
            axis.axhline(limit, color="#944632", linestyle="--", label="Comparison tolerance")
            axis.set(yscale="log", xlabel="Point index", title=title)
            axis.legend(fontsize=8)
        else:
            axis.text(.5, .5, "No paired evidence", ha="center", transform=axis.transAxes)
            axis.set(title=title, xticks=[], yticks=[])
    figure.suptitle(f"{record['case']} · Agreement with Lumerical")
    display(figure)
    plt.close(figure)


def show_versions(record):
    from IPython.display import Markdown, display

    rows = [(name, samples[0]["software"]["version"], samples[0]["software"].get("build", "—"),
             samples[0]["software"].get("gpu", samples[0]["software"]["device"]))
            for name, samples in record["solvers"].items()]
    display(Markdown(markdown_table(("Solver", "Version", "Build", "Device"), rows)))
