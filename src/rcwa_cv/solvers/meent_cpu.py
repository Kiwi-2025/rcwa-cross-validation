from importlib.metadata import version

import numpy as np

from ..conventions import result_from_amplitudes, wavevectors
from ..geometry import raster, rectangular_orders
from ..models import Layer


def probe():
    import meent
    return {"version": version("meent"), "device": "CPU"}


def solve(case, settings):
    import meent

    theta, phi = np.deg2rad([case.theta, case.phi])
    orders = rectangular_orders(case, settings)
    mx, my = orders.max(axis=0)
    layers = case.layers or (Layer(0, complex(case.incident)),)
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
    result = solver.conv_solve()
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
    return result_from_amplitudes(case, orders, amplitude, dict(probe(), formulation="continuous raster"),
                                  power, power.sum(axis=1))
