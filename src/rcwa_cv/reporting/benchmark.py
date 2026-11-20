"""Publish a complete suite as one numerical dataset and a Markdown report."""
import numpy as np

from ..case_loader import ROOT
from ..models import SimulationResult
from ..storage import read_json, write_json
from .observables import collect, COLUMNS
from .plots import save_figures
from .tables import (BASELINE, OPEN_SOLVERS, POWER_METRICS, compare_to_lumerical,
                     comparison_table, markdown_table, pretty, read_run, summarize)


def optical_data(result):
    """Preserve every propagating channel, with polarization axes defined in the dataset."""
    ports = {}
    for i, port in enumerate(("R", "T")):
        mask = result.propagating[i]
        amplitude = result.amplitude[i, mask]
        ports[port] = {"total": result.totals[i].tolist(), "orders": result.orders[mask].tolist(),
                       "power": result.power[i, mask].tolist(), "real": amplitude.real.tolist(),
                       "imag": amplitude.imag.tolist()}
    return ports


def read_sample(sample):
    """Reconstruct the propagating channels needed to report a published sample."""
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


def case_record(folder, manifest, results):
    pairs = compare_to_lumerical(manifest, results)
    solvers = {}
    for name, state in manifest["solvers"].items():
        samples = []
        for entry in state["completed"]:
            path = folder/entry["path"]
            point_id = entry["index"]
            metadata = read_json(path.with_suffix(".json"))
            refinements = []
            for step, refinement in enumerate(entry["refinements"], 1):
                settings = read_json(path.parent/f"{step:02d}_{refinement['axis']}.json")["settings"]
                refinements.append({**refinement, "settings":settings})
            samples.append({
                "point":point_id, "settings":metadata.get("settings"), "physics":entry["physics"],
                "converged":entry["converged"], "refinements":refinements,
                "timing":{key:metadata[key] for key in ("wall_seconds","compute_seconds","peak_allocated_bytes")
                          if key in metadata},
                **optical_data(results[name][point_id]),
            })
        solvers[name] = {"status":state["status"], "samples":samples}
    rows = collect(manifest, results)
    return {key:manifest[key] for key in ("case", "title", "run_id", "points", "lossy")} | {
        "summary":summarize(manifest, pairs), "pairs":pairs, "solvers":solvers,
        "observables":[dict(zip(COLUMNS, row, strict=True)) for row in rows],
    }


def reference_overview(cases):
    rows = []
    for name in OPEN_SOLVERS:
        pairs = [pair for case in cases for pair in case["pairs"]
                 if pair["solvers"] == [name, BASELINE] and pair["points"]]
        power = max((pair[key] for pair in pairs for key in POWER_METRICS), default=None)
        amplitude = max((pair["max_amplitude"] for pair in pairs), default=None)
        passes = sum(pair["status"] == "PASS" for pair in pairs)
        within = sum(max(pair[k] for k in (*POWER_METRICS, "max_amplitude")) <= 1e-3 for pair in pairs)
        rows.append((name, len(pairs), sum(pair["points"] for pair in pairs),
                     pretty(power), pretty(amplitude), within, passes))
    return markdown_table(("Solver vs Lumerical", "Cases", "Matched points", "Worst Δpower",
                           "Worst |Δamplitude|", "Cases with both deltas ≤ 1e-3", "Cases passed"), rows)


def conclusion(cases, has_periodic_diagnostics=False):
    planar = [case for case in cases if case["case"].startswith("A")]
    periodic = [case for case in cases if not case["case"].startswith("A")]
    pass_count = sum(case["summary"]["status"]=="PASS" for case in planar)
    inc_count = sum(case["summary"]["status"]=="INCONCLUSIVE" for case in periodic)
    planar_power = max((case["summary"]["max_power"] for case in planar
                        if case["summary"]["max_power"] is not None), default=None)
    planar_amp = max((case["summary"]["max_amplitude"] for case in planar
                      if case["summary"]["max_amplitude"] is not None), default=None)
    periodic_followup = (
        "**Meent diagnosis.** Controlled changes to Meent's finite-order material matrices "
        "explain the main differences at discontinuous interfaces. The study also measures the effect "
        "of Lumerical's actual Fourier order, resonance sensitivity in C02, and the B06 half-mesh phase offset. "
        "[Experiments and case-by-case findings](PERIODIC_DIAGNOSIS.md)."
        if has_periodic_diagnostics else
        "**Priority for further validation.** Densely sample the C02 resonances and refine Fourier order "
        "and geometry sampling independently. Resolve order-by-order power balance for C06 and check loss "
        "and polarization convergence for the metallic B05 and C01 cases."
    )
    return (
        f"**Planar validation.** {pass_count}/{len(planar)} cases pass against Lumerical. The largest absolute "
        f"power and complex-amplitude differences are {pretty(planar_power)} and {pretty(planar_amp)}.\n\n"
        f"**Periodic structures.** {inc_count}/{len(periodic)} cases are inconclusive under the reported "
        "settings. Agreement with Lumerical quantifies consistency for the sampled configurations. "
        "The periodic pass decision also requires convergence evidence from both solvers.\n\n"
        + periodic_followup
    )


def report_text(dataset, figures_by_case):
    cases = dataset["cases"]
    count = sum(len(case["points"]) for case in cases)
    rows = []
    for case in cases:
        case_id = case["case"]
        summary = case["summary"]
        rows.append((f"[{case_id}](#{case_id.lower()})", case["title"], len(case["points"]),
                     summary["coverage"], pretty(summary["max_power"]),
                     pretty(summary["max_amplitude"]), summary["status"]))
    sections = [
        "# RCWA Benchmark Against Lumerical",
        f"Profile **{dataset['profile']}** · **{count} excitation points** · "
        f"**{len(cases)} cases** · s and p incidence at each point. "
        "[Numerical dataset](results/benchmark.json) · [Periodic-case diagnosis](PERIODIC_DIAGNOSIS.md) · [Conclusion](#conclusion)",
        "Each reported difference uses Lumerical as the reference at the same excitation point. "
        "The quick profile retains the published solver settings. The [periodic study](PERIODIC_DIAGNOSIS.md) "
        "checks the effect of aligning the actual Fourier basis.",
        "## Case overview",
        markdown_table(("Case", "Optical problem", "Points", "Coverage", "Max Δpower",
                        "Max |Δamplitude|", "Status"), rows),
        "Power differences include total reflectance, transmittance, absorptance, and the efficiency of "
        "each propagating diffraction order. Amplitudes use the common power-normalized reference. "
        "A missing phase metric means that no matched channel exceeds the reporting floor. Point indices are zero-based.",
        "## Solver agreement with Lumerical",
        reference_overview(cases),
        "The common 1e-3 cutoff is descriptive. A pass also requires full coverage, the case-specific tolerance, "
        "the phase tolerance, and convergence evidence.",
        "## Software versions",
        markdown_table(("Software or runtime", "Version or device"), list(dataset["software"].items())),
        "## Case comparisons and figures",
    ]
    for case in cases:
        case_id = case["case"]
        case_dir = f"cases/{case_id[0]}/{case_id}"
        pictures = {
            path.name: f"![{case_id} {path.stem.replace('-', ' ')}]({path.relative_to(ROOT).as_posix()})"
            for path in figures_by_case[case_id]
        }
        sections.extend([
            f"### {case_id}",
            f'**{case["title"]}**',
            f"[Notebook, physical model and applications]({case_dir}/{case_id}.ipynb)"
            + (f" · [Diagnosis](PERIODIC_DIAGNOSIS.md#{case_id.lower()})" if case_id[0] in "BC" else ""),
            comparison_table(case["pairs"], len(case["points"])),
            pictures.pop("spectrum-0.png"),
            "<details>\n<summary>Geometry, additional spectra, diffraction orders and solver differences</summary>\n\n"
            + "\n\n".join(pictures.values()) + "\n\n</details>",
        ])
    sections.extend(["## Conclusion", conclusion(cases, "periodic_diagnostics" in dataset)])
    return "\n\n".join(sections) + "\n"


def publish_benchmark(folders):
    runs = [read_run(folder) for folder in folders]
    manifests = [manifest for manifest, _ in runs]
    first = manifests[0]
    engines = first["solvers"]
    for manifest in manifests:
        if (manifest["software"] != first["software"] or manifest["profile_settings"] != first["profile_settings"]
                or manifest["solvers"]["lumerical"]["build"] != engines["lumerical"]["build"]):
            raise ValueError("The benchmark used inconsistent settings or software versions.")
    software = dict(first["software"])
    lumerical = engines["lumerical"]
    torcwa = engines["torcwa"]
    software.update({"Lumerical RCWA": f"{lumerical['version']} / build {lumerical['build']}",
                     "PyTorch CUDA runtime": torcwa["cuda"], "torcwa device": torcwa["gpu"],
                     "Operating system": first["host"]})
    data = {"profile":first["profile"], "profile_settings":first["profile_settings"],
            "comparison_reference":BASELINE,
            "software":software, "point_index":"zero-based",
            "power_axes":["diffraction order","incident polarization (s, p)"],
            "amplitude_axes":["diffraction order","outgoing polarization (s, p)","incident polarization (s, p)"],
            "cases":[case_record(folder, manifest, results)
                     for folder, (manifest, results) in zip(folders, runs, strict=True)]}
    figures = {}
    for manifest, results in runs:
        case_id = manifest["case"]
        target = ROOT/"results"/"figures"/case_id
        figures[case_id] = save_figures(target, manifest, results, ROOT/"cases"/case_id[0]/case_id/"case.yaml")
    write_json(ROOT/"results"/"benchmark.json", data)
    (ROOT/"BENCHMARK_REPORT.md").write_text(report_text(data, figures), encoding="utf-8")


def refresh_published_report():
    """Refresh the comparisons from the preserved optical samples."""
    path = ROOT / "results/benchmark.json"
    data = read_json(path)
    data["comparison_reference"] = BASELINE
    figures = {}
    for case in data["cases"]:
        manifest = case | {"representative": False, "point_limit": None, "solvers": {
            name: {"status": state["status"], "completed": [
                {"index": sample["point"], "converged": sample["converged"], "physics": sample["physics"]}
                for sample in state["samples"]]}
            for name, state in case["solvers"].items()}}
        results = {name: {sample["point"]: read_sample(sample) for sample in state["samples"]}
                   for name, state in case["solvers"].items()}
        case["pairs"] = compare_to_lumerical(manifest, results)
        case["summary"] = summarize(manifest, case["pairs"])
        target = ROOT / "results/figures" / case["case"]
        generated = save_figures(target, manifest, results)
        supplements = [target / "geometry.png", *generated]
        resonance = target / "resonance-diagnosis.png"
        if case["case"] == "C02" and "periodic_diagnostics" in data and resonance.is_file():
            supplements.append(resonance)
        figures[case["case"]] = supplements
    write_json(path, data)
    (ROOT / "BENCHMARK_REPORT.md").write_text(report_text(data, figures), encoding="utf-8", newline="\n")
