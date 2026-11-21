from importlib.metadata import version

import numpy as np

from ..conventions import incident_basis, result_from_xy, wavevectors
from ..geometry import midpoint_phase, raster, rectangular_orders, shape_fourier_grid


def probe():
    import grcwa
    return {"version": version("grcwa"), "device": "CPU"}


def _li_layer(solver, pixels):
    from grcwa.fft_funs import get_conv
    from grcwa.rcwa import MakeKPMatrix, SolveLayerEigensystem

    order_count = len(solver.G)
    epsilon = get_conv(1 / pixels.size, pixels, solver.G)
    inverse_normal = np.linalg.inv(get_conv(1 / pixels.size, 1 / pixels, solver.G))
    longitudinal = np.linalg.inv(epsilon)
    transverse = np.zeros((2 * order_count, 2 * order_count), dtype=complex)
    # The magnetic field blocks Hx and Hy couple to Ey and Ex, respectively.
    transverse[:order_count, :order_count] = epsilon
    transverse[order_count:, order_count:] = inverse_normal
    kp = MakeKPMatrix(solver.omega, 1, longitudinal, solver.kx, solver.ky)
    solver.kp_list[1] = kp
    solver.q_list[1], solver.phi_list[1] = SolveLayerEigensystem(
        solver.omega, solver.kx, solver.ky, kp, transverse
    )


def _set_rectangular_basis(solver, orders):
    from grcwa.rcwa import Lattice_SetKs, MakeKPMatrix, SolveLayerEigensystem_uniform

    solver.G, solver.nG = orders, len(orders)
    k0 = solver.omega * np.sin(solver.theta) * np.sqrt(solver.Uniform_ep_list[0])
    solver.kx, solver.ky = Lattice_SetKs(
        orders, k0 * np.cos(solver.phi), k0 * np.sin(solver.phi), solver.Lk1, solver.Lk2
    )
    for kind, index, *properties in solver.id_list:
        if kind == 0:
            permittivity = solver.Uniform_ep_list[properties[0]]
            solver.kp_list[index] = MakeKPMatrix(solver.omega, 0, 1 / permittivity, solver.kx, solver.ky)
            solver.q_list[index], solver.phi_list[index] = SolveLayerEigensystem_uniform(
                solver.omega, solver.kx, solver.ky, permittivity
            )


def solve(case, settings, *, li_factorization=False, exact_shapes=False):
    import grcwa
    from grcwa.rcwa import GetSMatrix

    grcwa.set_backend("numpy")
    metadata = probe()
    theta, phi = np.deg2rad([case.theta, case.phi])
    lx, ly = case.period
    orders = rectangular_orders(case, settings)
    requested = len(orders)
    if case.dimensions < 2:
        ly = min(ly, lx / (4*max(1, settings.order)+4))
    solver = grcwa.obj(requested + (case.dimensions < 2), [lx, 0], [0, ly],
                       1/case.wavelength, theta, phi, verbose=0)
    solver.Add_LayerUniform(0, case.incident)
    pixels = []
    for layer in case.layers:
        if layer.shapes:
            grid = (shape_fourier_grid(layer, case, settings.grid, int(orders.max())) if exact_shapes else
                    raster(layer, case, settings.grid, midpoint=True))
            solver.Add_LayerGrid(layer.thickness, *grid.shape)
            pixels.append(grid.ravel())
        else:
            solver.Add_LayerUniform(layer.thickness, layer.epsilon)
    solver.Add_LayerUniform(0, case.exit)
    solver.Init_Setup(Gmethod=int(case.dimensions == 2))
    if case.dimensions == 2 and settings.order_y is not None:
        _set_rectangular_basis(solver, orders)
    if li_factorization:
        if case.dimensions != 1 or case.theta != 0 or len(case.layers) != 1 or len(pixels) != 1:
            raise ValueError("The Li adapter requires one patterned 1D layer at normal incidence.")
        _li_layer(solver, pixels[0][:, None])
        metadata["numerical_mode"] = "1D Li inverse rule"
    elif pixels:
        solver.GridLayer_geteps(np.concatenate(pixels))
    if exact_shapes:
        metadata["numerical_mode"] = "Exact shape Fourier coefficients"
    orders = solver.G
    zero = np.flatnonzero(np.all(orders == 0, axis=1))[0]
    source, kzi = incident_basis(case)
    transverse, kz2 = wavevectors(case, orders)
    fields = np.zeros((2, len(orders), 2, 2), complex)
    transmit, _, reflect, _ = GetSMatrix(0, solver.Layer_N-1, solver.q_list, solver.phi_list,
                                          solver.kp_list, solver.thickness_list)
    for p in range(2):
        magnetic = np.cross([*transverse[zero], kzi], source[:, p])
        columns = [zero, zero+len(orders)]
        modes = (reflect[:, columns] @ magnetic[:2], transmit[:, columns] @ magnetic[:2])
        for port, eps in enumerate((case.incident, case.exit)):
            mask = kz2[port] > 1e-10
            kz = np.sqrt(kz2[port, mask]) * (-1 if port == 0 else 1)
            k = np.column_stack((transverse[mask], kz))
            hx, hy = modes[port].reshape(2, -1)[:, mask]
            hz = -(k[:, 0]*hx + k[:, 1]*hy)/kz
            fields[port, mask, :, p] = (-np.cross(k, np.column_stack((hx, hy, hz)))/eps)[:, :2]
    fields *= midpoint_phase(orders, settings.grid)[None, :, None, None]
    return result_from_xy(case, orders, fields, dict(metadata, truncation="rectangular" if case.dimensions == 2 else "linear"))
