from ..solvers import MODULES
from ..storage import load_result, read_json
from ..validation.compare import differences, meets


POWER_METRICS = ("max_R", "max_T", "max_A", "max_order_power")
METRICS = (*POWER_METRICS, "max_amplitude", "max_phase_deg")
BASELINE = "lumerical"
OPEN_SOLVERS = tuple(name for name in MODULES if name != BASELINE)
PAIR_HEADERS = ("Solver vs Lumerical", "Matched points", "Max ΔR", "Max ΔT", "Max ΔA", "Max order ΔP",
                "Max |Δamplitude|", "Max phase Δ (deg)", "Worst amplitude point", "Status")


def markdown_table(headers, rows):
    lines = [headers, ["---"] * len(headers), *rows]
    return "\n".join("| " + " | ".join(str(x).replace("|", r"\|") for x in row) + " |" for row in lines)


def pretty(value):
    return "—" if value is None else f"{value:.3g}"


def read_run(folder):
    manifest = read_json(folder/"manifest.json")
    manifest["solvers"] = {name: state for name, state in manifest["solvers"].items()
                           if name in MODULES or name == "reference"}
    results = {name: {entry["index"]: load_result(folder/entry["path"])
                      for entry in state["completed"]}
               for name, state in manifest["solvers"].items()}
    return manifest, results


def reference_differences(results):
    reference = results.get(BASELINE, {})
    for name in OPEN_SOLVERS:
        samples = results.get(name, {})
        yield name, {index: differences(samples[index], reference[index])
                     for index in sorted(samples.keys() & reference.keys())}


def comparison_tolerance(case_id):
    return 1e-8 if case_id.startswith("A") else 1e-3


def compare_to_lumerical(manifest, results):
    pairs = []
    count = len(manifest["points"])
    tolerance = comparison_tolerance(manifest["case"])
    converged = {name: {row["index"] for row in state["completed"] if row["converged"]}
                 for name, state in manifest["solvers"].items()}
    for name, samples in reference_differences(results):
        pair = {"solvers": [name, BASELINE], "points": len(samples), "status": "NOT_RUN"}
        if samples:
            worst = max(samples, key=lambda i: samples[i]["max_amplitude"])
            pair.update({key: max((d[key] for d in samples.values() if d[key] is not None), default=None)
                         for key in METRICS})
            pair["worst_point"] = worst
            pair["worst_channel"] = samples[worst]["worst_amplitude_channel"]
            comparable = (len(samples) == count and samples.keys() <= (converged[name] & converged[BASELINE])
                          and all(d["complete"] for d in samples.values()))
            pair["status"] = ("PASS" if all(meets(d, tolerance) for d in samples.values()) else "FAIL"
                              ) if comparable else "INCONCLUSIVE"
        pairs.append(pair)
    return pairs


def summarize(manifest, pairs):
    evaluated = [pair for pair in pairs if pair["points"]]
    solver_states = manifest["solvers"]
    complete = sum(solver_states.get(name, {}).get("status") == "COMPLETE" for name in MODULES)
    subset = manifest["representative"] or manifest["point_limit"] is not None
    physics_fail = any(max(entry["physics"].values()) > 1e-6 for name, state in solver_states.items() if name in MODULES
                       for entry in state["completed"] if entry["converged"])
    if physics_fail or any(pair["status"] == "FAIL" for pair in pairs):
        status = "FAIL"
    elif pairs and complete == len(MODULES) and not subset and all(p["status"] == "PASS" for p in pairs):
        status = "PASS"
    else:
        status = "INCONCLUSIVE" if evaluated else "NOT_RUN"
    return {
        "status": status, "coverage": f"{complete}/{len(MODULES)}", "physics_failed": physics_fail,
        "max_power": max((p[key] for p in evaluated for key in POWER_METRICS), default=None),
        "max_amplitude": max((p["max_amplitude"] for p in evaluated), default=None),
    }


def comparison_table(pairs, point_count):
    rows = []
    for pair in pairs:
        rows.append([pair["solvers"][0], f"{pair['points']}/{point_count}",
                     *[pretty(pair.get(metric)) for metric in METRICS],
                     pair.get("worst_point", "—"), pair["status"]])
    return markdown_table(PAIR_HEADERS, rows)
