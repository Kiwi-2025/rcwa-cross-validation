"""Render the single benchmark from independently checked solver samples."""
import numpy as np

from ..case_loader import ROOT
from ..models import SimulationResult
from ..solvers import MODULES
from ..storage import read_json, write_json
from ..validation.compare import differences, meets
from .tables import BASELINE, OPEN_SOLVERS, POWER_METRICS, comparison_tolerance, markdown_table, pretty


DATASET = ROOT / "results" / "benchmark.json"


def optical_data(result):
    ports = {}
    for i, name in enumerate(("R", "T")):
        active = result.propagating[i]
        amplitude = result.amplitude[i, active]
        ports[name] = {"total": result.totals[i].tolist(), "orders": result.orders[active].tolist(),
                       "power": result.power[i, active].tolist(), "real": amplitude.real.tolist(),
                       "imag": amplitude.imag.tolist()}
    return ports


def read_sample(sample):
    """Reconstruct the propagating channels needed to report a saved sample."""
    ports = [sample["R"], sample["T"]]
    orders = sorted({tuple(order) for port in ports for order in port["orders"]})
    lookup = {order: index for index, order in enumerate(orders)}
    mask = np.zeros((2, len(orders)), dtype=bool)
    power = np.zeros((2, len(orders), 2))
    amplitude = np.zeros((2, len(orders), 2, 2), dtype=complex)
    for i, port in enumerate(ports):
        indices = [lookup[tuple(order)] for order in port["orders"]]
        if indices:
            mask[i, indices] = True
            power[i, indices] = port["power"]
            amplitude[i, indices] = np.asarray(port["real"]) + 1j * np.asarray(port["imag"])
    return SimulationResult(np.asarray(orders, dtype=int).reshape(-1, 2), mask, power, amplitude,
                            np.asarray([port["total"] for port in ports]), {})


def compare_certified(record, results=None):
    """Compare only independently certified observables at matching orders."""
    pairs = {name: [] for name in OPEN_SOLVERS}
    tolerance = comparison_tolerance(record["case"])
    references = record["solvers"][BASELINE]
    joint = record.get("joint_convergence", False)
    aligned = zip(references, *(record["solvers"][name] for name in OPEN_SOLVERS), strict=True)
    for index, (base, *entries) in enumerate(aligned):
        if not base["power_converged"]:
            continue
        candidates = dict(zip(OPEN_SOLVERS, entries, strict=True))
        eligible = {name: row for name, row in candidates.items() if row["power_converged"]}
        if not eligible or (joint and len(eligible) != len(OPEN_SOLVERS)):
            continue
        right = read_sample(base["sample"]) if results is None else results.get(BASELINE, {}).get(index)
        if right is None:
            continue
        verified = {}
        shared_full = all(row["full_converged"] for row in eligible.values())
        for name, candidate in eligible.items():
            left = read_sample(candidate["sample"]) if results is None else results.get(name, {}).get(index)
            if left is None:
                continue
            full = base["full_converged"] and (shared_full if joint else candidate["full_converged"])
            delta = differences(left, right, include_fields=full)
            if not delta["complete"]:
                continue
            power = max(delta[key] for key in POWER_METRICS)
            row = {"point": index, "power": power, "power_pass": power <= tolerance}
            if full:
                row.update(amplitude=delta["max_amplitude"], phase_deg=delta["max_phase_deg"],
                           full_pass=meets(delta, tolerance))
            verified[name] = row
        if not joint or len(verified) == len(OPEN_SOLVERS):
            for name, row in verified.items():
                pairs[name].append(row)
    return pairs


def pair_summary(rows):
    full = [row for row in rows if "full_pass" in row]
    return (len(rows), sum(row["power_pass"] for row in rows), len(full),
            sum(row["full_pass"] for row in full), max((row["power"] for row in rows), default=None),
            max((row["amplitude"] for row in full), default=None),
            max((row["phase_deg"] for row in full if row["phase_deg"] is not None), default=None))


def case_status(pairs, count):
    rows = [row for values in pairs.values() for row in values]
    if any(not row["power_pass"] or not row.get("full_pass", True) for row in rows):
        return "Outside tolerance"
    if sum("full_pass" in row for row in rows) == len(OPEN_SOLVERS) * count:
        return "Pass"
    return "Partial evidence" if rows else "Convergence unverified"


def setting_rows(record):
    lines = []
    for name, rows in record["solvers"].items():
        settings = [row["sample"]["settings"] for row in rows if "sample" in row]
        modes = sorted({row["sample"].get("numerical_mode", "native") for row in rows if "sample" in row})
        orders = sorted({(s["order"], s.get("order_y", s["order"])) for s in settings})
        half_orders = " / ".join(str(x) if x == y else f"{x}×{y}" for x, y in orders) or "—"
        ranges = [" / ".join(map(str, sorted({s[axis] for s in settings}))) or "—" for axis in ("grid", "slices")]
        pending = []
        unchecked = []
        unresolved = []
        for i, row in enumerate(rows):
            if "error" in row or "extension_error" in row:
                unchecked.append(str(i))
            if row["full_converged"]:
                continue
            failed = [
                check for check in row["refinements"]
                if not check.get("independent_native_mesh", True)
                or not meets(check, 1e-8 if record["case"].startswith("A") else 2.5e-4,
                             row.get("phase_refinement_tolerance_deg", .5 if record["case"].startswith("A") else .25))
            ]
            axes = list(dict.fromkeys(check["axis"] for check in failed))
            if row.get("mesh_checked") is False:
                axes.append("mesh pending")
            reasons = "run" if "error" in row else ", ".join(axes) or "physical checks"
            pending.append(f"{i} ({reasons})")
            unresolved.extend(failed)
        lines.append((name, ", ".join(modes) or "—", half_orders, *ranges,
                      sum(row["power_converged"] for row in rows), sum(row["full_converged"] for row in rows),
                      "; ".join(pending) or "—",
                      pretty(max((delta["max_amplitude"] for delta in unresolved), default=None)),
                      ", ".join(unchecked) or "—"))
    return lines


def solver_label(name, record):
    if name in record.get("native_solvers", {}):
        return f"{name} (Li adapter)"
    if any(row.get("sample", {}).get("numerical_mode", "").startswith("Exact shape") and row["power_converged"]
           for row in record["solvers"].get(name, ())):
        return f"{name} (exact shape at selected points)"
    return name


def case_table(pairs, count, record=None):
    lines = []
    for name, values in pairs.items():
        power, power_pass, full, full_pass, delta_power, amplitude, phase = pair_summary(values)
        label = solver_label(name, record) if record else name
        lines.append((label, f"{power}/{count}", power_pass, f"{full}/{count}", full_pass,
                      pretty(delta_power), pretty(amplitude), pretty(phase)))
    return markdown_table(("Solver vs Lumerical", "Power pairs", "Power passes", "Full pairs", "Full passes",
                           "Max Δpower", "Max complex-amplitude difference", "Max phase Δ (deg)"), lines)


def joint_settings_table(record):
    """Expose the exact settings used at every admitted class C point."""
    rows = []
    for entry in record["comparisons"]["meent"]:
        index = entry["point"]
        settings = []
        for name in (*OPEN_SOLVERS, BASELINE):
            sample = record["solvers"][name][index]["sample"]
            config = sample["settings"]
            x, y = config["order"], config.get("order_y", config["order"])
            order = str(x) if x == y else f"{x}×{y}"
            mode = " (exact geometry)" if sample["numerical_mode"].startswith("Exact shape") else ""
            settings.append(f"{order} / {config['grid']}{mode}")
        rows.append((index, "Full" if "full_pass" in entry else "Power", *settings))
    return markdown_table(("Point", "Common evidence", "Meent", "torcwa", "grcwa", "Lumerical"), rows) if rows else ""


def coverage_figure(records):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(9.2, 6.3), layout="constrained")
    FigureCanvasAgg(figure)
    for axis, key, title in zip(figure.subplots(1, 2), ("power_converged", "full_converged"),
                                ("Power evidence", "Power, amplitude and phase evidence"), strict=True):
        counts = np.array([[sum(row[key] for row in rec["solvers"][name]) for name in MODULES] for rec in records])
        lengths = np.array([len(rec["points"]) for rec in records])
        fraction = counts / lengths[:, None]
        axis.imshow(fraction, vmin=0, vmax=1, cmap="GnBu", aspect="auto")
        axis.set(xticks=range(len(MODULES)), xticklabels=list(MODULES),
                 yticks=range(len(records)), yticklabels=[rec["case"] for rec in records], title=title)
        for j, row in enumerate(counts):
            for i, value in enumerate(row):
                axis.text(i, j, f"{value}/{lengths[j]}", ha="center", va="center",
                          color="white" if fraction[j, i] > .7 else "#102d3b", fontsize=9)
    target = ROOT / "results/figures/convergence-coverage.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=155)


def agreement_figure(records):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(11, 7), layout="constrained")
    FigureCanvasAgg(figure)
    labels = [record["case"] for record in records]
    specs = (("Power", "power"), ("Complex amplitude", "amplitude"), ("Phase", "phase_deg"))
    for axis, (title, metric) in zip(figure.subplots(1, 3, sharey=True), specs, strict=True):
        for i, solver in enumerate(OPEN_SOLVERS):
            x, y = [], []
            for j, record in enumerate(records):
                values = [row.get(metric) for row in record["comparisons"][solver]]
                worst = max((value for value in values if value is not None), default=None)
                if worst is not None:
                    tolerance = .5 if metric == "phase_deg" else comparison_tolerance(record["case"])
                    x.append(max(worst / tolerance, 1e-12))
                    y.append(j + (i - 1) * .2)
            axis.scatter(x, y, s=25, label=solver)
        axis.axvline(1, color="#804437", linestyle="--", linewidth=1)
        axis.set(xscale="log", xlabel="Maximum difference / tolerance", title=title,
                 ylim=(len(records) - .5, -.5), yticks=range(len(records)), yticklabels=labels)
        axis.grid(axis="y", alpha=.2)
    figure.axes[-1].legend(loc="lower left", fontsize=8)
    figure.savefig(ROOT / "results/figures/convergence-agreement.png", dpi=155)


def class_c_figures(records):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.pyplot import close

    from ..case_loader import catalog
    from .plots import geometry_figure

    cases = [record for record in records if record["case"].startswith("C")]
    if not cases:
        return
    root = ROOT / "results" / "figures"
    figure = Figure(figsize=(10, 5.8), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(2, 3).flat
    observables = {
        "C01": ("wavelength_nm", "Wavelength (nm)", "Absorptance",
                lambda r, _: 1 - r.totals[:, 0].sum()),
        "C02": ("normalized_frequency", "Period / wavelength", "Transmitted power",
                lambda r, _: r.totals[1, 0]),
        "C03": ("radius_nm", "Pillar radius (nm)", "Transmission phase (deg)",
                lambda r, i: np.angle(r.amplitude[1, i, 0, 0], deg=True)),
        "C04": ("rotation_deg", "Fin angle (deg)", "Cross-polarized power",
                lambda r, i: abs(r.amplitude[1, i, 1, 0])**2),
        "C05": ("wavelength_nm", "Wavelength (nm)", "Phase shift from alignment (deg)",
                lambda r, i: np.angle(r.amplitude[1, i, 0, 0], deg=True)),
        "C06": ("wavelength_nm", "Wavelength (nm)", "First-order pair power", None),
    }
    for axis, record in zip(axes, cases, strict=True):
        case_id = record["case"]
        geometry = geometry_figure(catalog(case_id)[0])
        folder = root / case_id
        folder.mkdir(parents=True, exist_ok=True)
        geometry.savefig(folder / "geometry.png", dpi=125)
        close(geometry)

        key, x_label, y_label, value = observables[case_id]
        series = {}
        aligned = {}
        full_field = case_id in ("C03", "C04", "C05")
        for pair in record["comparisons"][OPEN_SOLVERS[0]]:
            if full_field and "full_pass" not in pair:
                continue
            index = pair["point"]
            point = record["points"][index]
            result = read_sample(record["solvers"][BASELINE][index]["sample"])
            orders = result.orders.tolist()
            if case_id == "C06":
                for label, targets in (("x orders", ([-1, 0], [1, 0])),
                                       ("y orders", ([0, -1], [0, 1]))):
                    indices = [orders.index(order) for order in targets]
                    total_power = result.power[1, indices, 0].sum()
                    series.setdefault(label, []).append((point[key], total_power))
            else:
                variant = point["variant"].replace("_", " ").capitalize()
                measured = value(result, orders.index([0, 0]))
                series.setdefault(variant, []).append((point[key], measured))
                if case_id == "C05" and point["variant"] == "nominal":
                    aligned[point[key]] = measured
        for name, values in series.items():
            if case_id == "C05":
                values = [(x, (y - aligned[x] + 180) % 360 - 180) for x, y in values if x in aligned]
            if not values:
                continue
            x, y = zip(*sorted(values))
            axis.plot(x, y, "o-", label=name, markersize=4)
        if len(series) > 1:
            axis.legend(fontsize=8)
        axis.set(xlabel=x_label, ylabel=y_label, title=case_id)
        axis.grid(alpha=.22)
    figure.suptitle("Representative two-dimensional responses · Lumerical, s incidence")
    figure.savefig(root / "class-c-responses.png", dpi=155)


def report_text(dataset):
    records = dataset["cases"]
    all_rows = [row for rec in records for rows in rec["comparisons"].values() for row in rows]
    total = sum(len(rec["points"]) for rec in records)
    full_count = sum("full_pass" in row for row in all_rows)
    followup = {record["case"] for record in records if any(
        "followup_plan" in row for rows in record["solvers"].values() for row in rows
    )}
    overview = []
    details = []
    group_summary = []
    for group, title in (("A", "Planar structures"), ("B", "One-dimensional periodic structures"),
                         ("C", "Two-dimensional periodic structures")):
        details.append(f"## {group} · {title}")
        if group == "C" and (ROOT / "results/figures/class-c-responses.png").is_file():
            details.append("![Representative class C optical responses](results/figures/class-c-responses.png)")
        group_records = [r for r in records if r["case"].startswith(group)]
        group_total = sum(len(record["points"]) for record in group_records) * len(OPEN_SOLVERS)
        group_pairs = [row for record in group_records for rows in record["comparisons"].values() for row in rows]
        power, power_pass, full, full_pass, *_ = pair_summary(group_pairs)
        group_summary.append((group, group_total, power, power_pass, full, full_pass))
        for rec in group_records:
            case_id = rec["case"]
            count = len(rec["points"])
            pairs = rec["comparisons"]
            rows = [row for values in pairs.values() for row in values]
            case_total = count * len(OPEN_SOLVERS)
            power_count = len(rows)
            full = sum("full_pass" in row for row in rows)
            status = case_status(pairs, count)
            if status == "Pass" and rec.get("native_solvers"):
                status = "Pass with Li adapters"
            overview.append((f"[{case_id}](#{case_id.lower()})", rec["title"], count,
                             f"{power_count}/{case_total}", f"{full}/{case_total}", status))
            coordinates = [" / ".join(f"{key}={value}" for key, value in point.items()) for point in rec["points"]]
            paired_points = [(solver_label(solver, rec), ", ".join(str(row["point"]) for row in samples) or "—",
                              ", ".join(str(row["point"]) for row in samples if "full_pass" in row) or "—")
                             for solver, samples in pairs.items()]
            geometry = f"results/figures/{case_id}/geometry.png"
            joint_settings = joint_settings_table(rec) if rec.get("joint_convergence") else ""
            details += [
                f"### {case_id}", f"**{rec['title']}**",
                f"[Notebook and physical model](cases/{group}/{case_id}/{case_id}.ipynb)",
                case_table(pairs, count, rec),
                "<details>\n<summary>Settings, unresolved points and geometry</summary>\n\n"
                + markdown_table(("Solver", "Mode", "Reported half-order", "Grid", "Slices",
                                  "Power certified", "Fully certified", "Unresolved point (axis)",
                                  "Max amplitude change in unresolved refinement", "Solver error at point"),
                                 setting_rows(rec))
                + "\n\n" + markdown_table(("Solver vs Lumerical", "Power point indices", "Full point indices"),
                                            paired_points)
                + ("\n\nCertified settings at compared points (half-order / grid)\n\n" + joint_settings
                   if joint_settings else "")
                + "\n\n" + markdown_table(("Point", "Excitation"), list(enumerate(coordinates)))
                + (f"\n\n![{case_id} geometry]({geometry})" if (ROOT / geometry).is_file() else "")
                + "\n\n</details>",
            ]
            if case_id == "B04":
                slice_checks = [
                    (solver, pretty(row["coarse_slice_probe"]["max_amplitude"]),
                     pretty(max(check["max_amplitude"] for check in row["refinements"]
                                if check["axis"] == "slices")))
                    for solver, samples in rec["solvers"].items() for row in samples if "coarse_slice_probe" in row
                ]
                if slice_checks:
                    details += [
                        "**Slice refinement at 620 nm.** Each change uses a fixed Fourier half-order of 148 and "
                        "a fixed transverse grid. The production setting is 128 slices and is checked in both directions.",
                        markdown_table(("Solver", "Amplitude change from 64 to 128 slices",
                                        "Largest change across 96, 128, and 192 slices"), slice_checks),
                    ]
            if rec.get("native_solvers"):
                native = rec | {"solvers": rec["solvers"] | rec["native_solvers"]}
                native_pairs = compare_certified(native)
                details += [
                    "**Default open-source modes.** The primary rows use the Li adapter where indicated. "
                    "The adapter replaces the material multiplication normal to the grating interface with "
                    "the inverse Fourier rule and uses each library's eigensolver and scattering calculation. "
                    "The default modes retain the following independently eligible comparisons.",
                    case_table({solver: native_pairs[solver] for solver in rec["native_solvers"]}, count),
                ]
                native_checks = [
                    (solver, i, check["coarse_settings"]["order"], check["fine_settings"]["order"],
                     check["fine_settings"]["grid"], pretty(max(check[key] for key in POWER_METRICS)),
                     pretty(check["max_amplitude"]))
                    for solver, samples in rec["solvers"].items() for i, sample in enumerate(samples)
                    for check in sample.get("native_order_probe", [])
                ]
                if native_checks:
                    details += ["Within-solver changes at higher default Fourier orders",
                                markdown_table(("Solver", "Point", "Coarse half-order", "Fine half-order", "Grid",
                                                "Max power change", "Max amplitude change"), native_checks)]
    notes = [
        "# RCWA Convergence Benchmark Against Lumerical",
        f"**{len(records)} cases · {total} excitation points · s and p incidence.** "
        "[Numerical data and refinement evidence](results/benchmark.json) · [Conclusion](#conclusion)",
        "An agreement row uses only common points with matching propagating orders and convergence "
        "evidence from both solvers. Power-only pairs contribute power metrics. Full pairs also "
        "contribute complex amplitude and phase. A dash indicates missing paired evidence.",
        "## Case overview",
        markdown_table(("Case", "Optical structure", "Points", "Power pairs", "Full pairs", "Status"), overview),
        "![Per-solver convergence coverage](results/figures/convergence-coverage.png)",
        "The agreement plot uses the largest difference among the eligible pairs for each solver and case. "
        "The dashed line marks the comparison tolerance."
        + (" The case tables identify where a Li adapter is used." if
           any(rec.get("native_solvers") for rec in records) else ""),
        "![Comparison differences divided by their acceptance tolerances](results/figures/convergence-agreement.png)",
        "## Verification method",
        f"The study uses {total} published excitation points. For A, homogeneous planar layers require "
        "only the zero transverse harmonic. The independent Fresnel or multilayer solution checks the "
        "computed result at each point. The absolute power and amplitude tolerance is 1e-8.",
        "For periodic structures, each active axis changes while the other settings are held fixed. "
        "The absolute refinement thresholds are 2.5e-4 in power and complex amplitude and 0.25° "
        "in eligible phase. The cross-solver thresholds are 1e-3 and 0.5°. Phase applies when both "
        "channel powers are at least 1e-4. The settings tables give within-solver changes for any "
        "remaining refinement limits. B uses solver-specific order, mesh, and slice refinements, "
        "including a 0.05° phase refinement at 920 nm for B03 Meent. "
        "[Ansys RCWA solver and Fourier settings](https://optics.ansys.com/hc/en-us/articles/12959229278611-RCWA-Solver-Simulation-Object)",
        "For B02 and B05, Lumerical uses its 2D Li mode with permuted transverse coordinates. "
        "The direct 2D and 3D controls agreed within 7.7e-12 in complex amplitude at the tested settings. "
        "B04 uses the staircase geometry in a single 2D polygon. The B field phase uses the common "
        "transverse origin after removing the native half-sample shift on propagating nonzero orders.",
        "## Software",
        markdown_table(("Software or runtime", "Version or device"), list(dataset["software"].items())),
    ]
    if any(record.get("joint_convergence") for record in records):
        notes.insert(3, "Class C requires all four solvers to certify the same observables at a point. "
                     "The three comparisons against Lumerical are admitted together.")
    followup_method = []
    if followup.intersection({"B02", "B05"}):
        followup_method.append(
            "The B02 and B05 follow-up uses two successive Fourier and raster refinements. "
            "[Li's Fourier factorization rules](https://opg.optica.org/josaa/abstract.cfm?uri=josaa-13-9-1870)"
        )
    if "B04" in followup:
        followup_method.append(
            "The B04 follow-up fixes the 128-slice staircase for the Fourier comparisons and uses the final "
            "reported Fourier basis for separate grid and slice tests. At 620 nm the slice study brackets the "
            "128-slice production setting with 96 and 192 slices. Meent uses half-order 128 at that point "
            "with 108 and 148 as adjacent checks."
        )
    if any(rec["case"].startswith("C") for rec in records):
        followup_method.append(
            "The representative two-dimensional cases use shallow, moderate-contrast structures. "
            "Each solver checks two successive Fourier refinements at fixed geometry resolution "
            "and doubles the transverse grid at fixed Fourier order. "
            "The production setting is the middle order in the first passing three-order window. "
            "C06 refines the x and y orders separately. Each checked setting must pass the "
            "energy, passivity, order-sum, and power normalization checks to 1e-6."
        )
    notes[-2:-2] = followup_method
    outside = [(record["case"], name, row["point"],
                pretty(row["power"]) if not row["power_pass"] else "—",
                pretty(row.get("amplitude")), pretty(row.get("phase_deg")))
               for record in records for name, rows in record["comparisons"].items() for row in rows
               if not row["power_pass"] or not row.get("full_pass", True)]
    end = [
        "## Conclusion",
        markdown_table(("Group", "Possible pairs", "Power pairs", "Power passes", "Full pairs", "Full passes"),
                       group_summary),
        f"Of {total * len(OPEN_SOLVERS)} possible pairs, {len(all_rows)} qualify for power comparison "
        f"and {full_count} qualify for the full comparison. "
        f"{sum(row['power_pass'] for row in all_rows)} power pairs and "
        f"{sum(row.get('full_pass', False) for row in all_rows)} full pairs meet their agreement tolerances.",
        "Cases passing every comparison with their original solver modes are "
        + (", ".join(row[0].split("]")[0][1:] for row in overview if row[-1] == "Pass") or "none") + ".",
    ]
    joint = [record for record in records if record.get("joint_convergence")]
    if joint:
        power_points = sum(len(record["comparisons"]["meent"]) for record in joint)
        full_points = sum(sum("full_pass" in row for row in record["comparisons"]["meent"]) for record in joint)
        all_points = sum(len(record["points"]) for record in joint)
        end.append(f"In class C, all four solvers qualify at {power_points}/{all_points} points for power and "
                   f"{full_points}/{all_points} points for power, complex amplitude, and phase together.")
    if outside:
        end += ["Eligible comparisons outside tolerance",
                markdown_table(("Case", "Solver", "Point", "Power difference above tolerance",
                                "Complex-amplitude difference", "Phase difference (deg)"), outside)]
    adapter_passes = [row[0].split("]")[0][1:] for row in overview if row[-1] == "Pass with Li adapters"]
    if adapter_passes:
        end += ["Cases passing every comparison with the indicated Li adapters are "
                + ", ".join(adapter_passes) + "."]
    return "\n\n".join([*notes, *details, *end]) + "\n"


def refresh_published_report(data=None):
    if data is None:
        data = read_json(DATASET)
    for case in data["cases"]:
        if case["case"].startswith("C"):
            case["joint_convergence"] = True
        case["comparisons"] = compare_certified(case)
    coverage_figure(data["cases"])
    agreement_figure(data["cases"])
    class_c_figures(data["cases"])
    report = report_text(data)
    write_json(DATASET, data)
    (ROOT / "BENCHMARK_REPORT.md").write_text(report, encoding="utf-8", newline="\n")
