from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from time import perf_counter
from uuid import uuid4
import os
import platform

import numpy as np
from threadpoolctl import threadpool_limits
import yaml

from .case_loader import ROOT, load_case, points, resolve
from .models import SolverSettings
from .references import multilayer
from .solvers import adapter
from .solvers.base import Unavailable
from .storage import read_json, save_result, write_json
from .validation.convergence import settings_series, check_axis, converged
from .validation.physics import checks


RUNS = ROOT/".runs"


def configure():
    path = ROOT/"configs/local.yaml"
    local = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}
    for k, env in {"device":"RCWA_CUDA_DEVICE", "lumapi_path":"LUMAPI_PATH"}.items():
        if k in local:
            os.environ.setdefault(env, str(local[k]))


def software_versions():
    versions = {"Python": platform.python_version()}
    for name in ("rcwa-cross-validation", "numpy", "scipy", "matplotlib", "PyYAML",
                 "threadpoolctl", "meent", "grcwa", "torcwa", "torch", "jupyterlab", "ipykernel"):
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            continue
    return versions


def run(path, solvers, profile_name, point_limit=None, representative=False, resume=None, run_root=RUNS):
    case = load_case(path)
    case_id = case["id"]
    profile = yaml.safe_load((ROOT/f"configs/{profile_name}.yaml").read_text(encoding="utf-8"))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid4().hex[:6]
    folder = run_root/case_id[0]/case_id/run_id
    selected = list(points(case, profile_name)) if not representative else [("nominal", {})]
    if point_limit is not None:
        selected = selected[:point_limit]
    manifest = {"case": case_id, "title": case["title"], "profile": profile_name,
                "run_id": run_id, "profile_settings": profile,
                "lossy": resolve(case, "nominal", {}, SolverSettings(0, 2, 1)).lossy,
                "representative": representative, "point_limit": point_limit,
                "requested_solvers": solvers, "host": platform.platform(), "software": software_versions(),
                "points": [], "solvers": {}}
    labels = ["reference", *solvers] if case["periodic_dimensions"] == 0 else solvers
    for variant, overrides in selected:
        point = resolve(case, variant, overrides, SolverSettings(0,2,1))
        manifest["points"].append({"variant": variant, "wavelength_nm": point.wavelength,
                                   "theta_deg": point.theta, "phi_deg": point.phi, **overrides})
    if resume:
        folder = resume
        existing = read_json(folder/"manifest.json")
        keys = ("case","profile","profile_settings","requested_solvers","points")
        if any(manifest[key] != existing.get(key) for key in keys) or load_case(folder/"resolved_case.yaml") != case:
            raise ValueError("Resume requires the original case, solver list, settings, and point selection.")
        manifest = existing
    else:
        folder.mkdir(parents=True)
        (folder/"resolved_case.yaml").write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
    for name in labels:
        if manifest["solvers"].get(name, {}).get("status") == "COMPLETE":
            continue
        print(f"{case_id} {name} ({len(selected)} points)", flush=True)
        base_info = {"completed": [], "errors": []}
        manifest["solvers"][name] = base_info
        try:
            backend = multilayer if name == "reference" else adapter(name)
            base_info.update(backend.probe() if name != "reference" else {"device": "CPU", "version": "analytic"})
            with ExitStack() as stack:
                stack.enter_context(threadpool_limits(limits=1, user_api="blas"))
                if name == "lumerical":
                    fdtd = stack.enter_context(backend.session())
                    base_info["build"] = fdtd.version()
                for j, (variant, overrides) in enumerate(selected):
                    try:
                        all_results = []
                        for step, (label, settings) in enumerate(settings_series(case, profile, name)):
                            point = resolve(case, variant, overrides, settings)
                            start = perf_counter()
                            measurement = backend.solve(point, settings)
                            measurement.metadata.setdefault("wall_seconds", perf_counter()-start)
                            if any(not np.all(np.isfinite(x)) for x in (
                                measurement.totals, measurement.power, measurement.amplitude)):
                                raise ValueError("The solver returned a non-finite propagating result.")
                            record = folder/name/f"{j:04d}"/f"{step:02d}_{label}.npz"
                            save_result(record, measurement)
                            write_json(record.with_suffix(".json"), {"settings":asdict(settings), **measurement.metadata})
                            all_results.append((label, measurement))
                        result = all_results[0][1]
                        refinements = check_axis(all_results[1:], result)
                        base_info["completed"].append({"index":j, "path":f"{name}/{j:04d}/00_base.npz",
                            "physics":checks(result, point.lossy), "refinements":refinements,
                            "converged": (case["periodic_dimensions"] == 0 or
                                          (profile_name != "quick" and converged(refinements)))})
                    except Exception as exc:
                        message = f"{type(exc).__name__}: {exc}"
                        base_info["errors"].append({"index":j, "error":message})
                        print(f"  Point {j}: {message}", flush=True)
            base_info["status"] = ("COMPLETE" if len(base_info["completed"])==len(selected) else
                                   "PARTIAL" if base_info["completed"] else "ERROR")
        except (Unavailable, ImportError) as exc:
            base_info.update(status="UNAVAILABLE", reason=str(exc))
        except Exception as exc:
            base_info.update(status="ERROR", reason=f"{type(exc).__name__}: {exc}")
            print(f"  {base_info['reason']}", flush=True)
        write_json(folder/"manifest.json", manifest)
    return folder


def import_lumerical(folder, index, source):
    from .solvers import lumerical

    manifest_path = folder/"manifest.json"
    manifest = read_json(manifest_path)
    if not 0 <= index < len(manifest["points"]):
        raise ValueError("The point index is outside the saved run.")
    existing = manifest["solvers"].get("lumerical", {}).get("completed", [])
    if any(entry["index"] == index for entry in existing):
        raise ValueError("This run already has Lumerical results for the requested point.")
    case = load_case(folder/"resolved_case.yaml")
    restored = dict(manifest["points"][index])
    variant = restored.pop("variant")
    point = resolve(case, variant, restored, SolverSettings(0,2,1))
    result = lumerical.import_mat(point, source)
    if any(not np.all(np.isfinite(arr)) for arr in (result.totals, result.power, result.amplitude)):
        raise ValueError("The imported file contains non-finite propagating results.")
    record = folder/"lumerical"/f"{index:04d}"/"00_base.npz"
    save_result(record, result)
    write_json(record.with_suffix(".json"), result.metadata)
    existing.append({"index":index, "path":record.relative_to(folder).as_posix(),
                     "physics":checks(result,point.lossy), "refinements":[],
                     "converged":case["periodic_dimensions"] == 0})
    manifest["solvers"]["lumerical"] = {"completed":existing, "errors":[],
        "device":result.metadata["device"], "version":result.metadata["version"], "build":result.metadata["build"],
        "status":"COMPLETE" if len(existing) == len(manifest["points"]) else "PARTIAL"}
    if "lumerical" not in manifest["requested_solvers"]:
        manifest["requested_solvers"].append("lumerical")
    write_json(manifest_path, manifest)
