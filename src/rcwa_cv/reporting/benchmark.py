"""Publish a complete suite as one numerical dataset and a Markdown report."""
from itertools import combinations

from ..case_loader import ROOT
from ..solvers import MODULES
from ..storage import read_json, write_json
from .observables import collect, COLUMNS
from .plots import save_figures
from .tables import POWER_METRICS, comparison_table, markdown_table, pairwise, pretty, read_run, summarize


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


def case_record(folder, manifest, results):
    pairs = pairwise(manifest, results)
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


def pair_overview(cases):
    rows = []
    for first, second in combinations(MODULES, 2):
        pairs = [(case, pair) for case in cases for pair in case["pairs"]
                 if set(pair["solvers"]) == {first, second} and pair["points"]]
        if pairs:
            power = max(pair[key] for _, pair in pairs for key in POWER_METRICS)
            amplitude = max(pair["max_amplitude"] for _, pair in pairs)
            threshold = sum(max(pair[k] for k in (*POWER_METRICS, "max_amplitude")) <= 1e-3
                            for _, pair in pairs)
            rows.append((f"{first} / {second}", len(pairs), pretty(power), pretty(amplitude), threshold))
    return markdown_table(("Solver pair", "Cases", "Worst Δpower", "Worst |Δamplitude|",
                           "Cases with both deltas ≤ 1e-3"), rows)


def conclusion(cases):
    planar = [case for case in cases if case["case"].startswith("A")]
    periodic = [case for case in cases if not case["case"].startswith("A")]
    pass_count = sum(case["summary"]["status"]=="PASS" for case in planar)
    inc_count = sum(case["summary"]["status"]=="INCONCLUSIVE" for case in periodic)
    planar_pairs = [pair for case in planar for pair in case["pairs"] if
                    "reference" in pair["solvers"] and pair["points"]]
    planar_power = max(pair[key] for pair in planar_pairs for key in POWER_METRICS)
    planar_amp = max(pair["max_amplitude"] for pair in planar_pairs)
    largest = max(periodic, key=lambda case: case["summary"]["max_power"])
    grid_pairs = [pair for case in periodic for pair in case["pairs"]
                  if set(pair["solvers"]) == {"grcwa", "torcwa"} and pair["points"]]
    grid_power = max(pair[key] for pair in grid_pairs for key in POWER_METRICS)
    grid_amp = max(pair["max_amplitude"] for pair in grid_pairs)
    return (
        f"**Planar validation.** {pass_count}/{len(planar)} cases pass. Against the independent Fresnel or "
        f"multilayer reference, the largest absolute power and complex-amplitude differences are "
        f"{pretty(planar_power)} and {pretty(planar_amp)}, respectively. This verifies the tested planar "
        "normalization, polarization and phase conventions.\n\n"
        f"**Periodic structures.** {inc_count}/{len(periodic)} cases are inconclusive under the reported "
        f"settings. The largest observed power discrepancy is {pretty(largest['summary']['max_power'])} "
        f"in {largest['case']} ({largest['title']}). Across the periodic cases, grcwa and torcwa differ "
        f"by at most {pretty(grid_power)} in power and {pretty(grid_amp)} in complex amplitude at the tested "
        "points. Their common raster can produce shared discretization error. These results support "
        "a comparison of consistency under the reported settings, with no overall accuracy ranking.\n\n"
        "**Priority for further validation.** Densely sample the C02 resonances and refine Fourier order "
        "and geometry sampling independently. Resolve order-by-order power balance for C06 and check loss "
        "and polarization convergence for the metallic B05 and C01 cases."
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
        "# RCWA Benchmark Report",
        f"Profile **{dataset['profile']}** · **{count} excitation points** · "
        f"**{len(cases)} cases** · s and p incidence at each point. "
        "[Numerical dataset](results/benchmark.json) · [Conclusion](#conclusion)",
        "## Case overview",
        markdown_table(("Case", "Optical problem", "Points", "Coverage", "Max Δpower",
                        "Max |Δamplitude|", "Status"), rows),
        "Power differences include total reflectance, transmittance, absorptance, and the efficiency of "
        "each propagating diffraction order. Amplitudes use the common power-normalized reference. "
        "A missing phase metric means that no matched channel exceeds the reporting floor.",
        "## Solver-pair overview",
        pair_overview(cases),
        "The last column counts cases for which both reported maximum differences are at most 1e-3. "
        "These counts summarize the sampled data. A periodic case still requires convergence evidence to pass.",
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
            f"[Physical context and application]({case_dir}/README.md) · [Notebook]({case_dir}/{case_id}.ipynb)",
            comparison_table(case["pairs"], len(case["points"])),
            pictures.pop("spectrum-0.png"),
            "<details>\n<summary>Geometry, additional spectra, diffraction orders and solver differences</summary>\n\n"
            + "\n\n".join(pictures.values()) + "\n\n</details>",
        ])
    sections.extend(["## Conclusion", conclusion(cases)])
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
