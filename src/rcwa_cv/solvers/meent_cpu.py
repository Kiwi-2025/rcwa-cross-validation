from importlib.metadata import version

import numpy as np

from ..conventions import result_from_amplitudes, wavevectors
from ..geometry import raster, rectangular_orders, shape_fourier_grid
from ..models import Layer


def probe():
    import meent
    return {"version": version("meent"), "device": "CPU"}


def solve(case, settings, *, material_operator="native", exact_shapes=False):
    import meent

    theta, phi = np.deg2rad([case.theta, case.phi])
    orders = rectangular_orders(case, settings)
    mx, my = orders.max(axis=0)
    layers = case.layers or (Layer(0, complex(case.incident)),)
    if exact_shapes:
        cells = [shape_fourier_grid(layer, case, settings.grid, int(max(mx, my))) for layer in layers]
        material_operator = "direct-dfs"
    else:
        cells = [
            (raster(layer, case, settings.grid, midpoint=True) if layer.shapes else
             np.full((settings.grid, settings.grid if case.dimensions == 2 else 1), layer.epsilon))
            for layer in layers
        ]
    # Meent expects (layer, y, x), with y descending and passive n-imaginary.
    index = np.sqrt(np.stack(cells)).conj().transpose(0, 2, 1)[:, ::-1, :].copy()
    solver = meent.call_mee(
        backend=0, n_top=np.sqrt(case.incident), n_bot=np.sqrt(case.exit),
        theta=theta, phi=phi, fto=(int(mx), int(my)), wavelength=case.wavelength,
        period=case.period, thickness=[layer.thickness for layer in layers],
        ucell=index, fourier_type=1, type_complex=np.complex128,
    )
    if material_operator == "native":
        result = solver.conv_solve()
    else:
        matrices = _direct_matrices(cells, index, int(mx), int(my), material_operator)
        result = solver.solve_for_conv(case.wavelength, matrices, matrices, np.linalg.inv(matrices))
    amplitude = np.zeros((2, len(orders), 2, 2), complex)
    power = np.zeros((2, len(orders), 2))
    transverse, kz2 = wavevectors(case, orders)
    kzi = np.sqrt(case.incident)*np.cos(theta)
    for i, columns in enumerate((result.res_te_inc, result.res_tm_inc)):
        for port, side in enumerate(("R", "T")):
            eps = case.incident if port == 0 else case.exit
            s = getattr(columns, f"{side}_s").T.ravel().conj()
            # The coupled formulation stores TM in a quadrature magnetic-field variable.
            p = -1j * getattr(columns, f"{side}_p").T.ravel().conj()/np.sqrt(eps)
            kx, ky = transverse.T
            # Meent uses atan(ky/kx), whose basis reverses when kx is negative.
            signs = np.where(kx < -1e-12, -1, 1)
            if case.phi == 0:
                signs = np.where(abs(kx) < 1e-12, 1, signs)
            normalize = np.sqrt(np.maximum(kz2[port], 0)**.5/kzi)
            amplitude[port, :, :, i] = np.column_stack((s, p)) * (signs*normalize)[:, None] * (-1 if i else 1)
            power[port, :, i] = getattr(columns, "de_ri" if port == 0 else "de_ti").T.ravel()
    formulation = "continuous raster" if material_operator == "native" else material_operator
    metadata = dict(probe(), formulation=formulation)
    if exact_shapes:
        metadata["numerical_mode"] = "Exact shape Fourier coefficients (direct operator)"
    return result_from_amplitudes(case, orders, amplitude, metadata,
                                  power, power.sum(axis=1))


def _direct_matrices(cells, index, mx, my, operator):
    """Diagnostic controls that preserve Meent's eigensolver and output adapter."""
    if operator == "direct-cfs":
        from meent.on_numpy.emsolver.convolution_matrix import cell_compression
        from meent.on_numpy.emsolver.fourier_analysis import cfs2d

        return np.stack([cfs2d(n**2, x, y, 1, 1, mx, my)
                         for n, x, y in map(cell_compression, index)])
    if operator != "direct-dfs":
        raise ValueError(f"Unknown diagnostic material operator: {operator}")
    # Meent flattens orders with x varying fastest and indexes coefficients by
    # column mode minus row mode. Conjugate the material for its field convention.
    # The midpoint phase centers the FFT cells.
    modes = np.array([(x, y) for y in range(-my, my+1) for x in range(-mx, mx+1)])
    dx, dy = (modes - modes[:, None]).transpose(2, 0, 1)
    return np.stack([
        np.fft.fft2(cell.conj())[dx, dy] / cell.size
        * np.exp(-1j*np.pi*(dx/cell.shape[0]+dy/cell.shape[1]))
        for cell in cells
    ])
