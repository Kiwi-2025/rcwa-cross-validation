from importlib.metadata import version

import numpy as np

from ..conventions import incident_basis, result_from_xy, wavevectors
from ..geometry import midpoint_phase, raster, rectangular_orders


def probe():
    import grcwa
    return {"version": version("grcwa"), "device": "CPU"}


def solve(case, settings):
    import grcwa

    grcwa.set_backend("numpy")
    metadata = probe()
    theta, phi = np.deg2rad([case.theta, case.phi])
    lx, ly = case.period
    requested = len(rectangular_orders(case, settings))
    if case.dimensions < 2:
        ly = min(ly, lx / (4*max(1, settings.order)+4))
    solver = grcwa.obj(requested + (case.dimensions < 2), [lx, 0], [0, ly],
                       1/case.wavelength, theta, phi, verbose=0)
    solver.Add_LayerUniform(0, case.incident)
    pixels = []
    for layer in case.layers:
        if layer.shapes:
            grid = raster(layer, case, settings.grid, midpoint=True)
            solver.Add_LayerGrid(layer.thickness, *grid.shape)
            pixels.append(grid.ravel())
        else:
            solver.Add_LayerUniform(layer.thickness, layer.epsilon)
    solver.Add_LayerUniform(0, case.exit)
    solver.Init_Setup(Gmethod=int(case.dimensions == 2))
    if pixels:
        solver.GridLayer_geteps(np.concatenate(pixels))
    orders = solver.G
    zero = np.flatnonzero(np.all(orders == 0, axis=1))[0]
    source, kzi = incident_basis(case)
    transverse, kz2 = wavevectors(case, orders)
    fields = np.zeros((2, len(orders), 2, 2), complex)
    for p in range(2):
        solver.MakeExcitationPlanewave(0, 0, 0, 0, order=int(zero))
        magnetic = np.cross([*transverse[zero], kzi], source[:, p])
        solver.a0[[zero, zero+len(orders)]] = magnetic[:2]
        modes = (solver.GetAmplitudes(0, 0)[1],
                 solver.GetAmplitudes(solver.Layer_N-1, 0)[0])
        for port, eps in enumerate((case.incident, case.exit)):
            mask = kz2[port] > 1e-10
            kz = np.sqrt(kz2[port, mask]) * (-1 if port == 0 else 1)
            k = np.column_stack((transverse[mask], kz))
            hx, hy = modes[port].reshape(2, -1)[:, mask]
            hz = -(k[:, 0]*hx + k[:, 1]*hy)/kz
            fields[port, mask, :, p] = (-np.cross(k, np.column_stack((hx, hy, hz)))/eps)[:, :2]
    fields *= midpoint_phase(orders, settings.grid)[None, :, None, None]
    return result_from_xy(case, orders, fields, dict(metadata, truncation="rectangular" if case.dimensions == 2 else "linear"))
