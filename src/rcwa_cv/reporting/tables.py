from itertools import combinations
import csv
import html
from shutil import copyfile
from statistics import median

from ..case_loader import ROOT, catalog, load_case
from ..solvers import MODULES
from ..storage import load_result, read_json, write_json
from ..validation.compare import differences, meets


METRICS = ("max_R", "max_T", "max_A", "max_order_power", "max_amplitude", "max_phase_deg")
PAIR_HEADERS = ("Solver pair", "Matched points", "Max R difference", "Max T difference", "Max A difference",
                "Max order-power difference", "Max complex-amplitude difference", "Max phase difference (deg)",
                "Worst amplitude point", "Worst amplitude channel", "Status")
CATEGORY_HEADERS = ("Case", "Solver coverage", "Max power difference", "Max complex-amplitude difference",
                    "Worst solver pair", "Convergence", "Status", "Source run")


def write_table(folder, name, headers, rows, heading, note=""):
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
    (folder/f"{name}.md").write_text(f"# {heading}\n\n{note}\n\n{markdown_table(headers, rows)}\n", encoding="utf-8")


def markdown_table(headers, rows):
    lines = [headers, ["---"] * len(headers), *rows]
    return "\n".join("| " + " | ".join(str(x).replace("|", r"\|") for x in row) + " |" for row in lines)


def pretty(x):
    return "—" if x is None else f"{x:.3g}"


def compare_run(folder):
    manifest = read_json(folder/"manifest.json")
    active = {name: state for name,state in manifest["solvers"].items() if name in MODULES or name=="reference"}
    available = {name: {row["index"]: (load_result(folder/row["path"]), row) for row in state["completed"]}
                 for name, state in active.items()}
    rows, pairs = [], []
    n = len(manifest["points"])
    for a, b in combinations(available, 2):
        left, right = available[a], available[b]
        shared = sorted(left.keys() & right.keys())
        pair = {"pair": f"{a} / {b}", "points":len(shared), "status":"NOT_RUN"}
        if shared:
            samples = {i: differences(left[i][0], right[i][0]) for i in shared}
            worst = max(shared, key=lambda i:samples[i]["max_amplitude"])
            pair.update({k:max((d[k] for d in samples.values() if d[k] is not None),default=None) for k in METRICS})
            pair.update(worst_point=worst, worst_condition=manifest["points"][worst],
                        worst_channel=samples[worst]["worst_amplitude_channel"])
            eligible = len(shared)==n and all(
                left[i][1]["converged"] and right[i][1]["converged"] and samples[i]["complete"] for i in shared)
            tol = 1e-8 if "reference" in available else 1e-3
            pair["status"] = ("PASS" if all(meets(d,tol) for d in samples.values()) else "FAIL") if eligible else "INCONCLUSIVE"
        pairs.append(pair)
        rows.append([pair["pair"], f"{len(shared)}/{n}", *[pretty(pair.get(k)) for k in METRICS],
                     f"{pair['worst_point']:04d}" if shared else "—", pair.get("worst_channel") or "—", pair["status"]])
    statuses = {name: state["status"] for name, state in active.items()}
    complete = sum(statuses.get(name)=="COMPLETE" for name in MODULES)
    all_complete = complete == len(MODULES)
    evaluated = [p for p in pairs if p["points"]]
    worst = max(evaluated, key=lambda p:p["max_amplitude"], default=None)
    physics_fail = any(max(e["physics"].values()) > 1e-6 for s in active.values()
                       for e in s["completed"] if e["converged"])
    subset = manifest["representative"] or manifest["point_limit"] is not None
    report_status = ("FAIL" if physics_fail or any(p["status"]=="FAIL" for p in pairs) else
                     "PASS" if pairs and all_complete and not subset and all(p["status"]=="PASS" for p in pairs) else
                     "INCONCLUSIVE" if evaluated else "NOT_RUN")
    max_power = max((p[k] for p in evaluated for k in METRICS[:4]), default=None)
    summary = {k:manifest[k] for k in ("case","title","profile","run_id","representative","point_limit")}
    summary.update(status=report_status, coverage=f"{complete}/{len(MODULES)}", max_power=max_power,
                   max_amplitude=None if worst is None else worst["max_amplitude"],
                   worst_pair=None if worst is None else worst["pair"], solvers=statuses,
                   converged=(all_complete and all(e["converged"] for s in active.values()
                                                    for e in s["completed"])),
                   physics_failed=physics_fail, pairs=pairs)
    write_json(folder/"comparison.json", summary)
    note = ("Power is normalized to incident flux. Phase is compared above the channel-power floor. "
            "Periodic quick runs give provisional differences. See [point coordinates](points.csv).")
    write_table(folder, "comparison", PAIR_HEADERS, rows, f"{manifest['case']} solver comparison", note)
    fields = list(dict.fromkeys(k for point in manifest["points"] for k in point))
    coordinates = [[f"{i:04d}", *(point.get(k,"") for k in fields)] for i,point in enumerate(manifest["points"])]
    write_table(folder, "points", ["Point",*fields], coordinates, "Benchmark point coordinates")
    return summary, rows


def generate_report(folder):
    from .plots import plot_report
    from .observables import collect, COLUMNS

    manifest = read_json(folder/"manifest.json")
    manifest["solvers"] = {name: state for name,state in manifest["solvers"].items()
                           if name in MODULES or name=="reference"}
    summary, rows = compare_run(folder)
    figures = plot_report(folder, manifest)
    observables = collect(folder, manifest)
    if observables:
        write_table(folder, "observables", COLUMNS, observables, "Case-specific observables")
    observations = '<p><a href="observables.csv">Case-specific observables</a></p>' if observables else ''
    save_diagnostics(folder, manifest)
    status = summary["status"]
    head = "".join(f"<th>{html.escape(column)}</th>" for column in PAIR_HEADERS)
    body = "".join("<tr>"+"".join(f"<td>{html.escape(str(value))}</td>" for value in row)+"</tr>" for row in rows)
    images = "".join(f'<img src="{path}" alt="Power and phase curves">' for path in figures)
    title = html.escape(manifest["title"])
    coverage = ", ".join(f"{name}: {state}" for name,state in summary["solvers"].items())
    (folder/"report.html").write_text(
        f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{title}</title>'
        '<style>body{font:16px system-ui;margin:2rem;color:#1c2638}table{border-collapse:collapse}'
        'td,th{padding:.5rem;border:1px solid #ccd4e0;text-align:right}th{background:#edf3fa}'
        'img{max-width:900px;width:100%;display:block}</style>'
        f'<h1>{manifest["case"]} · {title}</h1><p>{status} · {html.escape(coverage)}</p>'
        '<p><a href="manifest.json">Run manifest</a> · <a href="comparison.csv">Pairwise CSV</a> · '
        '<a href="timing.csv">Timing</a> · <a href="physics.csv">Physics checks</a> · '
        '<a href="convergence.csv">Refinement checks</a></p>'
        f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>{observations}{images}</html>',
        encoding="utf-8")
    return summary


def save_diagnostics(folder, manifest):
    timing, refinement, physics = [], [], []
    for name, state in manifest["solvers"].items():
        measurements = []
        for entry in state["completed"]:
            metadata = read_json((folder/entry["path"]).with_suffix(".json"))
            measurements.append(metadata)
            physics.append([name, entry["index"], *entry["physics"].values()])
            for step, level in enumerate(entry["refinements"], 1):
                sidecar = (folder/entry["path"]).parent/f"{step:02d}_{level['axis']}.json"
                level_value = read_json(sidecar)["settings"][level["axis"]]
                refinement.append([name, entry["index"], level["axis"], level_value,
                                   *[pretty(level["differences"][k]) for k in METRICS]])
        if measurements:
            wall = [m["wall_seconds"] for m in measurements if "wall_seconds" in m]
            effective = [m["compute_seconds"] for m in measurements if "compute_seconds" in m]
            memory = [m["peak_allocated_bytes"] for m in measurements if "peak_allocated_bytes" in m]
            timing.append([name, state.get("device", "Unknown"), len(measurements), pretty(median(wall) if wall else None),
                           pretty(median(effective) if effective else None), max(memory, default="—")])
    write_table(folder,"timing",
                ("Solver","Device","Points","Median adapter wall time (s)","Median measured compute (s)",
                 "Peak GPU allocation (bytes)"),timing,"Timing",
                "Adapter wall time may include process and data transfer overhead. Compute timing scopes vary by solver.")
    write_table(folder,"physics",
                ("Solver","Point","Order-sum error","Amplitude-power error","Conservation or passivity error",
                 "Negative power"),physics,"Physics checks")
    write_table(folder,"convergence",
                ("Solver","Point","Refinement axis","Coarser setting",*METRICS),refinement,"Refinement checks",
                "For each axis, every row compares a coarser setting with the finest setting.")


def update_categories(folders=()):
    preferred = {folder.parent.name: folder.name for folder in folders}
    rows_by_category = {}
    for path in catalog():
        case = load_case(path)
        id = case["id"]
        folder = ROOT/"results"/id[0]/id
        candidates = [r for p in folder.glob("*/comparison.json") if
                      set((r:=read_json(p))["solvers"]) <= (set(MODULES) | {"reference"})]
        chosen = max(candidates, key=lambda r: (r["point_limit"] is None,
            not r["representative"], r["coverage"]==f"{len(MODULES)}/{len(MODULES)}",
            r["profile"]=="convergence", r["run_id"]), default=None)
        if id in preferred:
            chosen = next(r for r in candidates if r["run_id"]==preferred[id])
        folder.mkdir(parents=True, exist_ok=True)
        rows_by_category.setdefault(id[0], []).append([
            f"{id} — {case['title']}", chosen["coverage"] if chosen else f"0/{len(MODULES)}",
            pretty(chosen["max_power"] if chosen else None), pretty(chosen["max_amplitude"] if chosen else None),
            (chosen["worst_pair"] or "—") if chosen else "—",
            ("Verified" if chosen.get("converged") else
             "Pending" if chosen["profile"]=="quick" else "Incomplete") if chosen else "—",
            chosen["status"] if chosen else "NOT_RUN",
            chosen["run_id"] if chosen else "—",
        ])
        if chosen:
            detail = folder/chosen["run_id"]
            for filename in ("comparison.md","comparison.csv","points.csv"):
                source = detail/filename
                if source.is_file():
                    (folder/filename).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        convergence_runs = [r for r in candidates if r["profile"] in ("pilot","convergence")]
        if convergence_runs:
            latest = max(convergence_runs, key=lambda r: (not r["representative"], r["profile"]=="convergence",
                                                         r["run_id"]))
            detail = folder/latest["run_id"]
            for source_name, filename in (("comparison","convergence-comparison"),("convergence","refinement"),
                                          ("points","convergence-points")):
                for extension in ("md","csv"):
                    source = detail/f"{source_name}.{extension}"
                    if source.is_file():
                        content = source.read_text(encoding="utf-8")
                        if filename == "convergence-comparison" and extension == "md":
                            content = content.replace("(points.csv)", "(convergence-points.csv)")
                        (folder/f"{filename}.{extension}").write_text(content, encoding="utf-8")
    for category, rows in rows_by_category.items():
        write_table(ROOT/"results"/category, "consistency", CATEGORY_HEADERS, rows,
                    f"Category {category} consistency",
                    "Each row uses the most complete available run. See the case folder for pairwise results. "
                    "INCONCLUSIVE includes quick comparisons without convergence evidence.")
    links = "\n".join(f"- [Category {c} consistency]({c}/consistency.md)" for c in rows_by_category)
    (ROOT/"results/README.md").write_text(
        "# RCWA solver consistency results\n\n"+links+"\n\n"
        "The tables identify each source run. See the repository README for the full benchmark and software versions.\n",
        encoding="utf-8")


def publish_benchmark(folders):
    """Update the repository summary and case plots from one complete benchmark invocation."""
    from .plots import save_geometry

    summaries = [read_json(folder/"comparison.json") for folder in folders]
    manifests = [read_json(folder/"manifest.json") for folder in folders]
    versions = manifests[0]["software"]
    engines = {name: manifests[0]["solvers"][name] for name in MODULES}
    for manifest in manifests:
        if manifest["software"] != versions or any(
            manifest["solvers"][name].get("build") != engines[name].get("build") for name in MODULES
        ):
            raise ValueError("The benchmark used different software versions across cases.")
    lumerical = engines["lumerical"]
    torch = engines["torcwa"]
    version_rows = [(name, label) for name, label in versions.items()]
    version_rows.extend([
        ("Lumerical RCWA", f"{lumerical['version']} / build {lumerical['build']}"),
        ("PyTorch CUDA runtime", torch["cuda"]),
        ("torcwa device", torch["gpu"]),
        ("Operating system", manifests[0]["host"]),
    ])
    rows = []
    for folder, summary, manifest in zip(folders, summaries, manifests, strict=True):
        group, case_id = summary["case"][0], summary["case"]
        case_dir = ROOT/"cases"/group/case_id
        figures = case_dir/"figures"
        figures.mkdir(exist_ok=True)
        for source in (folder/"figures").glob("*.png"):
            copyfile(source, figures/source.name)
        save_geometry(case_dir/"case.yaml", figures/"geometry.png")
        if (folder/"observables.csv").is_file():
            copyfile(folder/"observables.csv", folder.parent/"observables.csv")
        rows.append([
            f"[{case_id}](cases/{group}/{case_id}/{case_id}.ipynb)", summary["title"], len(manifest["points"]),
            summary["coverage"], pretty(summary["max_power"]), pretty(summary["max_amplitude"]),
            summary["status"], f"[Table](results/{group}/{case_id}/comparison.md)",
        ])
    readme = ROOT/"README.md"
    before, after = readme.read_text(encoding="utf-8").split("<!-- BEGIN BENCHMARK -->")
    _, rest = after.split("<!-- END BENCHMARK -->")
    content = markdown_table(
        ("Case", "Benchmark", "Points", "Solvers", "Max power difference", "Max complex-amplitude difference",
         "Status", "Details"), rows)
    profile = manifests[0]["profile"]
    count = sum(row[2] for row in rows)
    version_table = markdown_table(("Software or runtime", "Version or device"), version_rows)
    text = (f"Profile **{profile}**, {count} points across {len(rows)} cases. Each point includes s and p incidence.\n\n"
            f"{content}\n\n"
            "The maximum power difference includes total R, T, A and propagating-order efficiency. "
            "Nonconverged periodic results are marked INCONCLUSIVE.\n\n"
            f"### Software versions for this benchmark\n\n{version_table}\n")
    readme.write_text(f"{before}<!-- BEGIN BENCHMARK -->\n\n{text}\n<!-- END BENCHMARK -->{rest}", encoding="utf-8")
