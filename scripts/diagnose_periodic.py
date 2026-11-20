"""Reproduce targeted periodic-case sensitivity and material-operator controls."""
from argparse import ArgumentParser
from contextlib import ExitStack
from dataclasses import asdict, replace

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from meent.on_numpy.emsolver.convolution_matrix import to_conv_mat_raster_continuous
from scipy.signal import find_peaks
from threadpoolctl import threadpool_limits

from rcwa_cv.case_loader import ROOT, catalog, load_case, resolve
from rcwa_cv.geometry import raster
from rcwa_cv.models import SolverSettings
from rcwa_cv.reporting.benchmark import optical_data
from rcwa_cv.runner import configure, software_versions
from rcwa_cv.solvers import grcwa_cpu, lumerical, meent_cpu, torcwa_cuda
from rcwa_cv.storage import read_json, write_json
from rcwa_cv.validation.compare import differences
from rcwa_cv.validation.physics import checks


def metrics(left, right):
    delta = differences(left, right)
    return {
        "power": max(delta[key] for key in ("max_R", "max_T", "max_A", "max_order_power")),
        "amplitude": delta["max_amplitude"],
        "phase_deg": delta["max_phase_deg"],
        "matched_orders": delta["complete"],
    }


def native_axis_exchange_error(case, settings):
    """Check that Meent's transverse material operators interchange under x ↔ y."""
    cells = np.stack([
        np.sqrt(raster(layer, case, settings.grid, midpoint=True)).conj().T[::-1, :]
        for layer in case.layers
    ])
    order = settings.order
    eps_x, eps_y, inv_eps_z = to_conv_mat_raster_continuous(cells, order, order)
    side = 2 * order + 1
    swap = np.arange(side**2).reshape(side, side).T.ravel()
    swap_y = eps_y[:, swap][:, :, swap]
    swap_z = inv_eps_z[:, swap][:, :, swap]
    return {
        "transverse_relative_max": float(abs(eps_x - swap_y).max() / abs(eps_x).max()),
        "longitudinal_relative_max": float(abs(inv_eps_z - swap_z).max() / abs(inv_eps_z).max()),
    }


def matched_lumerical_basis(case, settings, reference, published):
    matched = lumerical.solve(case, settings, match_fourier_order=True)
    native_orders = np.asarray(matched.metadata["native_orders"])
    bound = np.abs(native_orders).max(axis=0).tolist()
    expected = [settings.order, settings.order if case.dimensions == 2 else 1]
    if bound != expected:
        raise RuntimeError(f"{case.id} requested native bounds {expected}, returned {bound}.")
    return {
        "native_bounds": bound,
        "native_orders": len(native_orders),
        "relative_to_grcwa": metrics(reference, matched),
        "relative_to_published_basis": metrics(published, matched),
        "transmittance": matched.totals[1].tolist(),
    }


def run_case(record, include_lumerical):
    case_id = record["case"]
    spec = load_case(catalog(case_id)[0])
    worst = max(record["pairs"], key=lambda pair: pair["max_amplitude"])
    index = worst["worst_point"]
    point = dict(record["points"][index])
    variant = point.pop("variant")
    one_dimensional = spec["periodic_dimensions"] == 1
    base = SolverSettings(8,128,8) if one_dimensional else SolverSettings(3,96,8)
    refined = SolverSettings(12,256,8) if one_dimensional else SolverSettings(4,192,8)
    fine = SolverSettings(32,512,8) if one_dimensional else SolverSettings(6,384,8)
    grids = {"quick":base,
             "order":replace(base, order=refined.order),
             "grid":replace(base, grid=refined.grid),
             "combined":refined,
             "finer_open":fine}
    if case_id == "B04":
        grids["slices"] = replace(refined, slices=32)
        grids["finer_open"] = replace(fine, slices=32)
    if case_id == "B05":
        grids["finer_open"] = replace(fine, order=48)
    results = {}
    snapshot = {}
    for label, settings in grids.items():
        case = resolve(spec, variant, point, settings)
        solvers = {"meent":meent_cpu.solve, "grcwa":grcwa_cpu.solve}
        if label == "quick":
            solvers["torcwa"] = torcwa_cuda.solve
        if include_lumerical and label != "finer_open":
            solvers["lumerical"] = lumerical.solve
        values = {name:solve(case, settings) for name, solve in solvers.items()}
        results[label] = values
        reference = values["grcwa"]
        snapshot[label] = {
            "settings":asdict(settings),
            "relative_to_grcwa":{name:metrics(reference, value) for name,value in values.items() if name!="grcwa"},
            "physics":{name:checks(value, case.lossy) for name,value in values.items()},
            "lumerical_native_orders":len(values["lumerical"].metadata["native_orders"]) if "lumerical" in values else None,
        }
    case = resolve(spec, variant, point, base)
    reference = results["quick"]["grcwa"]
    matched_basis = (
        matched_lumerical_basis(case, base, reference, results["quick"]["lumerical"])
        if include_lumerical else None
    )
    controls = {mode:metrics(reference, meent_cpu.solve(case, base, material_operator=mode))
                for mode in ("direct-cfs","direct-dfs")}
    sensitivity = {}
    for label in ("order","grid","combined","finer_open","slices"):
        if label not in results:
            continue
        origin = results["combined" if label=="slices" else "quick"]
        sensitivity[label] = {name:metrics(origin[name], value) for name,value in results[label].items()
                              if name in origin}
    # Fourfold-symmetric cells should have equal normal-incidence total power
    # for the two orthogonal incident polarizations.
    symmetry = {}
    axis_exchange = {}
    if case_id in ("C01","C02","C03"):
        for label in ("quick","combined","finer_open"):
            symmetry[label] = {name:float(np.max(abs(v.totals[:,0]-v.totals[:,1])))
                               for name,v in results[label].items()}
            local_settings = grids[label]
            symmetric_case = resolve(spec, variant, point, local_settings)
            axis_exchange[label] = native_axis_exchange_error(symmetric_case, local_settings)
    return {"case":case_id, "point_index":index, "point":{"variant":variant,**point},
            "worst_amplitude_channel":worst["worst_channel"], "settings":snapshot,
            "solver_sensitivity":sensitivity, "meent_controls_at_quick":controls,
            "fourfold_symmetry":symmetry, "meent_native_axis_exchange":axis_exchange,
            "lumerical_matched_basis": matched_basis}


def c02_spectrum(include_lumerical):
    spec = load_case(catalog("C02")[0])
    frequency = np.linspace(.514,.538,49)
    traces = []
    open_solvers = {"meent": meent_cpu.solve, "grcwa": grcwa_cpu.solve}
    profiles = [(3, 96, open_solvers), (6, 384, open_solvers)]
    if include_lumerical:
        profiles.extend([(3, 96, {"lumerical": lumerical.solve}),
                         (4, 192, {"lumerical": lumerical.solve})])
    for order, grid, solvers in profiles:
        settings = SolverSettings(order,grid,1)
        samples = [resolve(spec,"nominal",{"normalized_frequency":float(f)},settings) for f in frequency]
        for name,solve in solvers.items():
            values = np.asarray([solve(c,settings).totals[1] for c in samples])
            peaks = []
            for polarization, column in zip(("s","p"), values.T, strict=True):
                positions, props = find_peaks(column,prominence=.04)
                peaks.extend({"polarization":polarization, "frequency":float(frequency[i]),
                              "transmittance":float(column[i]),"prominence":float(prominence)}
                             for i,prominence in zip(positions,props["prominences"],strict=True))
            traces.append({"solver":name,"settings":asdict(settings),"transmission":values.tolist(),"sampled_peaks":peaks})
            print(f"C02 spectrum: {name} M={order}, N={grid}",flush=True)
    return {"normalized_frequency":frequency.tolist(),"traces":traces}


def translated_case(include_lumerical):
    spec = load_case(catalog("B01")[0])
    settings = SolverSettings(8,128,1)
    case = resolve(spec,"nominal",{"wavelength_nm":620},settings)
    layer, = case.layers
    shape, = layer.shapes
    shifted = replace(case,layers=(replace(layer,shapes=(replace(shape,center=(case.period[0]/4,0)),)),))
    output = {}
    solvers = {"meent":meent_cpu.solve,"grcwa":grcwa_cpu.solve,"torcwa":torcwa_cuda.solve}
    if include_lumerical:
        solvers["lumerical"] = lumerical.solve
    for name,solve in solvers.items():
        before = solve(case,settings)
        after = solve(shifted,settings)
        phase = np.exp(1j*np.pi/2*after.orders[:,0])
        restored = replace(after,amplitude=after.amplitude*phase[None,:,None,None])
        output[name] = metrics(before,restored)
    return {"case":"B01","shift_nm":case.period[0]/4,"translation_covariance":output}


def plot_c02_spectrum(spectrum):
    figure = Figure(figsize=(10, 4.2), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(1, 2, sharex=True, sharey=True)
    colors = {"grcwa": "#006da8", "meent": "#c54a20", "lumerical": "#17744f"}
    for trace in spectrum["traces"]:
        name = trace["solver"]
        order = trace["settings"]["order"]
        grid = trace["settings"]["grid"]
        line = "--" if order == 3 else "-"
        half_order = 2 * order + 1 if name == "lumerical" else order
        for axis, transmission in zip(axes, np.asarray(trace["transmission"]).T, strict=True):
            axis.plot(spectrum["normalized_frequency"], transmission, line,
                      label=f"{name}, M={half_order}, N={grid}", color=colors[name], linewidth=1.8)
    for axis, polarization in zip(axes, ("s", "p"), strict=True):
        axis.axvline(0.526, color="0.65", linewidth=0.9)
        axis.set(title=f"{polarization} incidence", xlabel="Normalized frequency P / λ₀",
                 ylim=(0, 1.05))
        axis.grid(alpha=0.18)
    axes[0].set_ylabel("Total transmittance")
    axes[1].legend(loc="upper right", fontsize=8)
    target = ROOT / "results/figures/C02/resonance-diagnosis.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=180)


def fit_phase_ramp(reference, candidate, period):
    """Fit a lateral phase ramp without changing the original channel amplitudes."""
    order, angle, weight = [], [], []
    before = after = 0.0
    channels = []
    for left, right in zip(reference, candidate, strict=True):
        for port in ("R", "T"):
            a, b = left[port], right[port]
            if not a["orders"]:
                continue
            f = np.array(a["real"]) + 1j * np.array(a["imag"])
            g = np.array(b["real"]) + 1j * np.array(b["imag"])
            for i, diffraction_order in enumerate(a["orders"]):
                if diffraction_order not in b["orders"]:
                    continue
                j = b["orders"].index(diffraction_order)
                m = diffraction_order[0]
                channels.append((m, f[i], g[j]))
                strength = np.minimum(abs(f[i])**2, abs(g[j])**2)
                for phase, power in zip(np.angle(g[j]*f[i].conj())[strength >= 1e-4],
                                        strength[strength >= 1e-4], strict=True):
                    order.append(m)
                    angle.append(phase)
                    weight.append(power)
    m, phase, w = map(np.array, (order, angle, weight))
    slope = float(np.sum(w * m * phase) / np.sum(w * m * m))
    for order_index, f, g in channels:
        before = max(before, float(abs(f - g).max()))
        after = max(after, float(abs(f - g * np.exp(-1j * order_index * slope)).max()))
    return {
        "phase_per_order_deg": float(np.rad2deg(slope)),
        "equivalent_x_shift_nm": -slope * period / (2 * np.pi),
        "phase_rms_residual_deg": float(np.rad2deg(np.sqrt(np.average((phase - slope * m)**2, weights=w)))),
        "max_amplitude_before": before,
        "max_amplitude_after": after,
    }


def c04_rotation_control():
    spec = load_case(catalog("C04")[0])
    rows = []
    for angle in (22.5, 45.0, 67.5):
        for order, grid in ((3, 96), (6, 384)):
            settings = SolverSettings(order, grid, 1)
            case = resolve(spec, "nominal", {"rotation_deg": angle}, settings)
            mirror = resolve(spec, "nominal", {"rotation_deg": -angle}, settings)
            reference = grcwa_cpu.solve(case, settings)
            same_angle = lumerical.solve(case, settings, match_fourier_order=True)
            opposite_angle = lumerical.solve(mirror, settings, match_fourier_order=True)
            rows.append({"angle_deg": angle, "settings": asdict(settings),
                         "same_angle": metrics(reference, same_angle),
                         "opposite_angle": metrics(reference, opposite_angle)})
    return rows


def b06_index_sampling(fdtd, case, settings):
    script = lumerical.build_script(case, settings).replace(
        'run("RCWA");', 'setnamed("RCWA", "report index", 1);\nrun("RCWA");', 1,
    )
    # Retrieve individual fields because RCWA reports z at interfaces and
    # index values at the midpoints of those interfaces.
    fdtd.eval(script + '\nprofile = getresult("RCWA", "index");'
             '\nsampled_x = profile.x; sampled_index = profile.index_z;')
    x_nm = np.asarray(fdtd.getv("sampled_x")).ravel() * 1e9
    index = np.asarray(fdtd.getv("sampled_index")).squeeze()
    epsilon = (index[:, :, 1]**2).mean(axis=1)
    first_harmonic = (epsilon * np.exp(-2j * np.pi * x_nm / case.period[0])).mean()
    step = float(np.diff(x_nm).mean())
    return {
        "reported_x_samples": len(x_nm),
        "reported_x_step_nm": step,
        "half_step_phase_deg": 180 * step / case.period[0],
        "material_first_harmonic_phase_deg": float(np.angle(first_harmonic, deg=True)),
    }


def b06_phase_controls(records, fdtd):
    record = next(case for case in records if case["case"] == "B06")
    spec = load_case(catalog("B06")[0])
    period = spec["period_nm"][0]
    archived = fit_phase_ramp(record["solvers"]["grcwa"]["samples"],
                              record["solvers"]["lumerical"]["samples"], period)
    output = {"archived_quick_sweep": archived}
    if fdtd is not None:
        settings = SolverSettings(8, 128, 1)
        point = {"theta_deg": 12.0}
        case = resolve(spec, "nominal", point, settings)
        reference = optical_data(grcwa_cpu.solve(case, settings))
        mesh = []
        for size in (64, 128, 256, 512):
            # Keep the 128 geometry strips fixed and change only the native mesh.
            native_settings = replace(settings, grid=size)
            value = optical_data(lumerical.solve(case, native_settings))
            mesh.append({"mesh_cells_x": size,
                         **fit_phase_ramp([reference], [value], period),
                         **b06_index_sampling(fdtd, case, native_settings)})
        output["fixed_geometry_mesh_sweep"] = mesh
        output["fixed_geometry_strips"] = settings.grid
        output["fixed_geometry_theta_deg"] = point["theta_deg"]
        print("B06 Lumerical mesh controls complete", flush=True)
    return output


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--open-only", action="store_true",
                        help="Use the three open-source solvers for new calculations.")
    args = parser.parse_args()
    configure()
    path = ROOT/"results/benchmark.json"
    dataset = read_json(path)
    records = []
    fdtd = None
    with ExitStack() as stack:
        stack.enter_context(threadpool_limits(limits=1,user_api="blas"))
        versions = software_versions()
        gpu = torcwa_cuda.probe()
        versions.update({"torcwa device": gpu["gpu"], "PyTorch CUDA runtime": gpu["cuda"]})
        if not args.open_only:
            fdtd = stack.enter_context(lumerical.session())
            versions["Lumerical RCWA"] = f"{lumerical.probe()['version']} / build {fdtd.version()}"
        for record in dataset["cases"]:
            if record["case"][0] not in "BC":
                continue
            records.append(run_case(record, not args.open_only))
            print(f"{record['case']} controls complete",flush=True)
        translation = translated_case(not args.open_only)
        b06_phase = b06_phase_controls(dataset["cases"], fdtd)
        spectrum = c02_spectrum(not args.open_only)
        rotation = c04_rotation_control() if not args.open_only else []
    dataset["periodic_diagnostics"] = {
        "software":versions,
        "scope":"open-source solvers" if args.open_only else "all four solvers",
        "point_selection":"Largest absolute complex-amplitude discrepancy in the quick benchmark for each case.",
        "reference_for_control":"grcwa at the same numerical settings, used as a matched operator control.",
        "cases":records, "translation_control":translation, "c02_spectrum":spectrum,
        "b06_phase_ramp":b06_phase,
        "c04_rotation_control": rotation,
    }
    write_json(path,dataset)
    plot_c02_spectrum(spectrum)
    print(f"Updated {path}",flush=True)


if __name__ == "__main__":
    main()
