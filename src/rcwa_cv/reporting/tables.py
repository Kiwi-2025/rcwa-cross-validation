from itertools import combinations

from ..solvers import MODULES
from ..storage import load_result, read_json
from ..validation.compare import differences, meets


POWER_METRICS = ("max_R", "max_T", "max_A", "max_order_power")
METRICS = (*POWER_METRICS, "max_amplitude", "max_phase_deg")
PAIR_HEADERS = ("Solver pair", "Matched points", "Max ΔR", "Max ΔT", "Max ΔA", "Max order ΔP",
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


def pairwise(manifest, results):
    pairs = []
    count = len(manifest["points"])
    tolerance = 1e-8 if "reference" in results else 1e-3
    converged = {name: {row["index"] for row in state["completed"] if row["converged"]}
                 for name, state in manifest["solvers"].items()}
    for left, right in combinations(results, 2):
        shared = sorted(results[left].keys() & results[right].keys())
        pair = {"solvers": [left, right], "points": len(shared), "status": "NOT_RUN"}
        if shared:
            samples = {i: differences(results[left][i], results[right][i]) for i in shared}
            worst = max(shared, key=lambda i: samples[i]["max_amplitude"])
            pair.update({key: max((d[key] for d in samples.values() if d[key] is not None), default=None)
                         for key in METRICS})
            pair["worst_point"] = worst
            pair["worst_channel"] = samples[worst]["worst_amplitude_channel"]
            comparable = (len(shared) == count and set(shared) <= (converged[left] & converged[right])
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
    physics_fail = any(max(entry["physics"].values()) > 1e-6 for state in solver_states.values()
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
        rows.append([" / ".join(pair["solvers"]), f"{pair['points']}/{point_count}",
                     *[pretty(pair.get(metric)) for metric in METRICS],
                     pair.get("worst_point", "—"), pair["status"]])
    return markdown_table(PAIR_HEADERS, rows)
