from importlib.metadata import version
from time import perf_counter
import os

import numpy as np

from .base import Unavailable
from ..conventions import incident_basis, result_from_xy, wavevectors
from ..geometry import midpoint_phase, raster, rectangular_orders


def probe():
    try:
        import torch
        import torcwa
    except ImportError as exc:
        raise Unavailable("Install the cuda extra for torcwa.") from exc
    if not torch.cuda.is_available():
        raise Unavailable("CUDA is required for torcwa. Install a CUDA-enabled PyTorch wheel.")
    device = torch.device(os.getenv("RCWA_CUDA_DEVICE", "cuda:0"))
    if device.type != "cuda":
        raise ValueError("RCWA_CUDA_DEVICE must specify a CUDA device.")
    gpu = torch.cuda.get_device_properties(device)
    return {"version": version("torcwa"), "torch": torch.__version__, "cuda": torch.version.cuda,
            "device": str(device), "gpu": gpu.name, "precision": "complex128", "tf32": False}


def _exterior_matrix(sim, case, settings, torch, device):
    # The native product can omit interior coupling matrices for a far-field sweep.
    empty = [[], []]
    scattering = None
    for layer in case.layers:
        eps = (torch.as_tensor(raster(layer, case, settings.grid, midpoint=True), device=device)
               if layer.shapes else layer.epsilon)
        sim.add_layer(layer.thickness, eps=eps)
        layer_matrix = [sim.layer_S11[0], sim.layer_S21[0], sim.layer_S12[0], sim.layer_S22[0]]
        scattering = layer_matrix if scattering is None else sim._RS_prod(scattering, layer_matrix, empty, empty)[0]
        for name in ("eps_conv", "mu_conv", "P", "Q", "kz_norm", "E_eigvec", "H_eigvec", "Cf", "Cb",
                     "layer_S11", "layer_S21", "layer_S12", "layer_S22"):
            getattr(sim, name).clear()
    scattering = sim._RS_prod(sim.Sin, scattering, empty, empty)[0]
    sim.S = sim._RS_prod(scattering, sim.Sout, empty, empty)[0]


def solve(case, settings):
    metadata = probe()
    import torch
    import torcwa

    device = torch.device(metadata["device"])
    torch.backends.cuda.matmul.allow_tf32 = False
    orders = rectangular_orders(case, settings)
    source, _ = incident_basis(case)
    _, kz2 = wavevectors(case, orders)
    mx, my = orders.max(axis=0)
    fields = np.zeros((2, len(orders), 2, 2), complex)
    torch.cuda.synchronize(device)
    torch.cuda.reset_peak_memory_stats(device)
    start = perf_counter()
    with torch.no_grad():
        sim = torcwa.rcwa(1/case.wavelength, [int(mx), int(my)], case.period,
                         dtype=torch.complex128, device=device)
        # Replace the released constructor's truncated pi in the propagation phase.
        sim.omega = 2*np.pi/case.wavelength
        metadata["wavenumber"] = "full-precision 2*pi/lambda"
        sim.add_input_layer(eps=case.incident)
        sim.add_output_layer(eps=case.exit)
        sim.set_incident_angle(*np.deg2rad([case.theta, case.phi]))
        if len(case.layers) > 1:
            _exterior_matrix(sim, case, settings, torch, device)
        else:
            for layer in case.layers:
                eps = (torch.as_tensor(raster(layer, case, settings.grid, midpoint=True), device=device)
                       if layer.shapes else layer.epsilon)
                sim.add_layer(layer.thickness, eps=eps)
            sim.solve_global_smatrix()
        for n, port in enumerate(("reflection", "transmission")):
            mask = kz2[n] > 1e-10
            if not mask.any():
                continue
            data = torch.stack([sim.S_parameters(orders[mask], port=port, polarization=pol, power_norm=False)
                                for pol in ("xx", "xy", "yx", "yy")], dim=-1)
            fields[n, mask] = data.cpu().numpy().reshape(-1, 2, 2) @ source[:2]
    torch.cuda.synchronize(device)
    metadata.update(compute_seconds=perf_counter()-start, peak_allocated_bytes=torch.cuda.max_memory_allocated(device))
    fields *= midpoint_phase(orders, settings.grid)[None, :, None, None]
    return result_from_xy(case, orders, fields, metadata)
