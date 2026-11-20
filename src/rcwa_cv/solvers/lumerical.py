from contextlib import contextmanager
from functools import lru_cache
import importlib.util
from pathlib import Path
import json
import os
from time import perf_counter

import numpy as np

from .base import Unavailable
from ..conventions import result_from_amplitudes, result_from_xy, wavevectors
from ..models import Layer


@lru_cache
def load_api():
    configured = os.getenv("LUMAPI_PATH")
    if configured:
        paths = [Path(configured)]
    else:
        root = Path(os.getenv("ProgramFiles", r"C:\Program Files"))
        paths = sorted([
            *(root / "ANSYS Inc").glob("v*/Lumerical/api/python/lumapi.py"),
            *(root / "Lumerical").glob("*/api/python/lumapi.py"),
            *Path("/opt/lumerical").glob("*/api/python/lumapi.py"),
        ], reverse=True)
    for path in paths:
        if path.is_file():
            spec = importlib.util.spec_from_file_location("lumapi", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module, path
    raise Unavailable("Set LUMAPI_PATH to the installed lumapi.py.")


def probe():
    _, path = load_api()
    return {"version": path.parents[3].name, "device": "CPU"}


_session = None


@contextmanager
def session():
    """Reuse the CAD process for a sweep and release the license on exit."""
    global _session
    if _session is not None:
        yield _session
        return
    api, _ = load_api()
    with api.FDTD(hide=True) as fdtd:
        _session = fdtd
        try:
            yield fdtd
        finally:
            _session = None


def _value(value):
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (tuple, list)):
        return "[" + ",".join(_value(item) for item in value) + "]"
    return f"{value:.17g}"


def build_script(case, settings, output=None, *, match_fourier_order=False):
    """Generate a standalone LSF model from the resolved benchmark point."""
    lines = ["# Generated RCWA benchmark. Run in a new Lumerical FDTD document.",
             "switchtolayout;", "deleteall;"]
    nm = 1e-9
    lx, ly = case.period
    material_names = {}

    def add(command, **properties):
        lines.append(f"{command};")
        lines.extend(f'set("{key.replace("_", " ").replace("multi coefficient", "multi-coefficient")}",{_value(value)});'
                     for key, value in properties.items())

    def material(eps):
        if eps.imag == 0 and eps.real > 0:
            return dict(material="<Object defined dielectric>", index=eps.real**.5)
        if eps not in material_names:
            n = np.sqrt(eps)
            name = f"RCWAcv_fixed_{n.real:.7g}_{n.imag:.7g}"
            lines.extend([f'if (!materialexists("{name}")) {{', 'mat=addmaterial("(n,k) Material");',
                          f'setmaterial(mat,"name","{name}");',
                          f'setmaterial("{name}","Refractive Index",{n.real:.17g});',
                          f'setmaterial("{name}","Imaginary Refractive Index",{n.imag:.17g});', '}'])
            material_names[eps] = name
        return dict(material=material_names[eps])

    def rectangle(x, y, wx, wy, z0, z1, eps, mesh_order=2, angle=0):
        mat = material(eps)
        add("addrect", x=x*nm, y=y*nm, x_span=wx*nm, y_span=wy*nm,
            z_min=z0*nm, z_max=z1*nm, first_axis="z", rotation_1=angle,
            override_mesh_order_from_material_database=1, mesh_order=mesh_order, **mat)

    # An interface-only model needs a finite pair of interface planes.
    start = -1 if not case.layers else 0
    layers = case.layers or (Layer(1, complex(case.incident)),)
    z = start
    rectangle(0, 0, 2*lx, 2*ly, start-100, start, complex(case.incident))
    rectangle(0, 0, 2*lx, 2*ly, case.thickness, case.thickness+100, complex(case.exit))
    interfaces = [start]
    for layer in layers:
        top = z + layer.thickness
        if layer.epsilon != 1:
            rectangle(0, 0, 2*lx, 2*ly, z, top, layer.epsilon, mesh_order=3)
        for shape in layer.shapes:
            x, y = shape.center
            if shape.kind == "circle":
                mat = material(shape.epsilon)
                add("addcircle", x=x*nm, y=y*nm, radius=shape.width*nm/2,
                    z_min=z*nm, z_max=top*nm, override_mesh_order_from_material_database=1,
                    mesh_order=1, **mat)
            else:
                for cx in (x-lx, x, x+lx):
                    if abs(cx) - shape.width/2 >= lx/2 + 1e-9:
                        continue
                    rectangle(cx, y, shape.width, shape.length if case.dimensions == 2 else 2*ly,
                              z, top, shape.epsilon, 1, shape.rotation)
        z = top
        interfaces.append(z)
    # The v252 rectangular solver interprets these values as half-orders.
    # Keep the published profile unless the diagnostic requests a matched basis.
    # The minimum native ky half-order is 1. Invariant geometries couple only
    # within the incident ky sector, which also supports conical incidence.
    native_order = settings.order if match_fourier_order else 2 * settings.order + 1
    add("addrcwa", name="RCWA", simulation_region="3D", propagation_axis="z",
        propagation_direction="forward", x=0, y=0, x_span=lx*nm, y_span=ly*nm,
        z_min=(start-20)*nm, z_max=(case.thickness+20)*nm,
        interface_position="absolute", interface_absolute_positions=[z*nm for z in interfaces],
         k_vectors_domain="rectangular", max_number_ku=native_order if case.dimensions else 1,
         max_number_kv=native_order if case.dimensions == 2 else 1,
        mesh_type="custom", mesh_cells_x=max(10, settings.grid if case.dimensions else 2),
        mesh_cells_y=max(10, settings.grid if case.dimensions == 2 else 2), mesh_cells_z=10,
        fit_materials_with_multi_coefficient_model=0,
        incident_angle="single", angle_theta=case.theta, angle_phi=case.phi,
        frequency_center=299792458/(case.wavelength*nm), frequency_span=0,
        frequency_points=1, report_grating_power=1, report_grating_characterization=1,
        report_grating_orders=1, report_field_amplitudes=1)
    lines += ['run("RCWA");', 'power=getresult("RCWA","grating_power");',
              'amplitudes=getresult("RCWA","grating_characterization");',
              'totals=getresult("RCWA","total_energy");',
              'modes=getresult("RCWA","grating_orders");',
              'fields=getresult("RCWA","field_amplitudes");']
    if output:
        lines.append(f"matlabsave({json.dumps(Path(output).as_posix())},power,amplitudes,totals,modes,fields);")
    return "\n".join(lines) + "\n"


def _dataset_orders(dataset):
    n = np.asarray(dataset["n"]).astype(int).ravel()
    m = np.asarray(dataset["m"]).astype(int).ravel()
    return [(int(x), int(y)) for x in n for y in m]


def normalize(case, power, amplitudes, totals, modes, fields, metadata):
    orders = np.array(_dataset_orders(modes), int)
    keys = {tuple(pair): i for i, pair in enumerate(orders)}
    transverse, kz2 = wavevectors(case, orders)
    native_k = np.column_stack([np.asarray(modes[f"k{a}"]).ravel() for a in "xy"])
    if not np.allclose(native_k, transverse, rtol=1e-9, atol=1e-10):
        raise ValueError("Lumerical diffraction coordinates do not match the benchmark lattice.")
    if not np.isclose(np.asarray(totals["lambda"]).item()*1e9, case.wavelength, rtol=1e-9):
        raise ValueError("Lumerical wavelength does not match the requested benchmark point.")
    for key, expected in (("theta", case.theta), ("phi", case.phi)):
        if not np.isclose(np.asarray(totals[key]).item(), expected, atol=1e-8):
            raise ValueError(f"Lumerical {key} does not match the requested benchmark point.")
    if set(_dataset_orders(amplitudes)) != set(keys):
        raise ValueError("Lumerical grating characterization and native order lists differ.")
    eff = np.zeros((2, len(orders), 2))
    tangential = np.zeros((2, len(orders), 2, 2), complex)
    for port, side in enumerate(("R", "T")):
        for source, p in enumerate("sp"):
            for field, pair in zip(np.asarray(power[f"{side}{p}_power"]).ravel(), _dataset_orders(power), strict=True):
                eff[port, keys[pair], source] = field.real
            for component, cartesian in enumerate("xy"):
                direction = "b" if port == 0 else "f"
                for field, pair in zip(np.asarray(fields[f"ek{cartesian}_{direction}{p}"]).ravel(),
                                       _dataset_orders(fields), strict=True):
                    # Ansys defines source s as k cross the surface normal.
                    tangential[port, keys[pair], component, source] = field * (-1 if p == "s" else 1)
    # Native diffraction fields use the lower transverse unit-cell corner.
    tangential *= np.where(orders.sum(axis=1) % 2, -1, 1)[None, :, None, None]
    amp = result_from_xy(case, orders, tangential, metadata).amplitude
    if not case.layers:
        kzi = np.sqrt(kz2[0, np.all(orders == 0, axis=1)][0])
        amp *= np.exp(-2j*np.pi/case.wavelength*(np.sqrt(kz2.clip(0)) + kzi)[:, :, None, None])
        amp[1] *= np.exp(2j*np.pi/case.wavelength*np.sqrt(kz2[1].clip(0))[:, None, None])
    total = np.array([[np.asarray(totals[f"{side}{p}"]).item().real for p in "sp"] for side in "RT"])
    keep = np.ones(len(orders), bool)
    if case.dimensions < 2:
        keep &= orders[:, 1] == 0
    if not case.dimensions:
        keep &= orders[:, 0] == 0
    metadata["native_orders"] = orders.tolist()
    return result_from_amplitudes(case, orders[keep], amp[:, keep], metadata, eff[:, keep], total)


def solve(case, settings, *, match_fourier_order=False):
    if _session is None:
        with session():
            return solve(case, settings, match_fourier_order=match_fourier_order)
    start = perf_counter()
    script = build_script(case, settings, match_fourier_order=match_fourier_order)
    _session.eval(script)
    datasets = [_session.getv(key) for key in ("power", "amplitudes", "totals", "modes", "fields")]
    return normalize(case, *datasets, dict(probe(), build=_session.version(), compute_seconds=perf_counter()-start))


def import_mat(case, path):
    """Load native datasets through Lumerical, including MATLAB v7.3 files."""
    with session() as fdtd:
        fdtd.matlabload(str(path.resolve()))
        datasets = [fdtd.getv(key) for key in ("power", "amplitudes", "totals", "modes", "fields")]
        return normalize(case, *datasets, dict(probe(), build=fdtd.version(), imported=True))
