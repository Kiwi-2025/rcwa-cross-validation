from importlib.metadata import version
from time import perf_counter
import os

import numpy as np

from .base import Unavailable
from ..conventions import incident_basis, result_from_xy, wavevectors
from ..geometry import midpoint_phase, raster, rectangular_orders, shape_fourier_grid


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


def _exterior_matrix(sim, case, layer_pixels, *, compact):
    # The native product can omit interior coupling matrices for a far-field sweep.
    empty = [[], []]
    scattering = None
    for layer in case.layers:
        if compact and scattering is not None and not layer.shapes and layer.epsilon == 1:
            scattering = sim._vacuum_gap(scattering, layer.thickness)
            continue
        eps = layer_pixels(layer)
        sim.add_layer(layer.thickness, eps=eps)
        layer_matrix = [sim.layer_S11[0], sim.layer_S21[0], sim.layer_S12[0], sim.layer_S22[0]]
        for name in ("eps_conv", "mu_conv", "P", "Q", "kz_norm", "E_eigvec", "H_eigvec", "Cf", "Cb",
                     "layer_S11", "layer_S21", "layer_S12", "layer_S22"):
            getattr(sim, name).clear()
        scattering = layer_matrix if scattering is None else sim._RS_prod(scattering, layer_matrix, empty, empty)[0]
    if hasattr(sim, "Sin"):
        scattering = sim._RS_prod(sim.Sin, scattering, empty, empty)[0]
    if hasattr(sim, "Sout"):
        scattering = sim._RS_prod(scattering, sim.Sout, empty, empty)[0]
    sim.S = scattering


def _li_solver(torcwa, torch):
    class LiRCWA(torcwa.rcwa):
        def add_layer(self, thickness, eps):
            self.inverse_normal = torch.linalg.inv(self._material_conv(eps.reciprocal()))
            super().add_layer(thickness, eps)

        def _eigen_decomposition(self):
            epsilon = self.eps_conv[-1]
            zero = torch.zeros_like(epsilon)
            eye = self.mu_conv[-1]
            kx = self.Kx_norm
            # Use the inverse rule on Ex. Ey and Ez use direct multiplication.
            p = torch.cat((torch.cat((zero, eye - kx @ torch.linalg.solve(epsilon, kx)), dim=1),
                           torch.cat((-eye, zero), dim=1)), dim=0)
            q = torch.cat((torch.cat((zero, kx @ kx - epsilon), dim=1),
                           torch.cat((self.inverse_normal, zero), dim=1)), dim=0)
            values, vectors = torch.linalg.eig(p @ q)
            kz = values.sqrt()
            self.P.append(p)
            self.Q.append(q)
            self.kz_norm.append(torch.where(kz.imag < 0, -kz, kz))
            self.E_eigvec.append(vectors)

    return LiRCWA


def _compact_solver(rcwa, torch):
    class ExteriorRCWA(rcwa):
        def _vacuum_gap(self, scattering, thickness):
            kz = torch.sqrt(1 - self.Kx_norm_dn**2 - self.Ky_norm_dn**2)
            kz = torch.where(kz.imag < 0, kz.conj(), kz)
            phase = torch.exp(1j * self.omega * kz * thickness).repeat(2)
            forward_t, forward_r, reverse_r, reverse_t = scattering
            return [phase[:, None] * forward_t, forward_r, phase[:, None] * reverse_r * phase,
                    reverse_t * phase]

        def _solve_layer_smatrix(self):
            electric = self.E_eigvec[-1]
            kz = self.kz_norm[-1]
            propagation = torch.exp(1j * self.omega * kz * self.thickness[-1])
            self.Q.clear()
            self.eps_conv.clear()
            self.mu_conv.clear()
            field = torch.linalg.solve(self.P.pop(), electric * kz)
            field = torch.linalg.solve(self.Vf, field)
            diagonal = electric + field
            off_diagonal = (electric - field) * propagation
            del field
            # The native coupling system is [D O; O D]. Its even and odd
            # blocks are D + O and D - O, with the same exterior scattering.
            even = torch.linalg.solve((diagonal + off_diagonal).mT,
                                      (electric * (1 + propagation)).mT).mT
            odd = torch.linalg.solve((diagonal - off_diagonal).mT,
                                     (electric * (1 - propagation)).mT).mT
            transmission = even - odd
            reflection = even + odd
            reflection.diagonal().sub_(1)
            self.layer_S11.append(transmission)
            self.layer_S21.append(reflection)
            self.layer_S12.append(reflection)
            self.layer_S22.append(transmission)

    return ExteriorRCWA


def solve(case, settings, *, li_factorization=False, exact_shapes=False, compact=None):
    metadata = probe()
    import torch
    import torcwa

    device = torch.device(metadata["device"])
    rcwa = torcwa.rcwa
    if li_factorization:
        if case.dimensions != 1 or case.theta != 0 or len(case.layers) != 1 or not case.layers[0].shapes:
            raise ValueError("The Li adapter requires one patterned 1D layer at normal incidence.")
        rcwa = _li_solver(torcwa, torch)
        metadata["numerical_mode"] = "1D Li inverse rule"
    if exact_shapes:
        metadata["numerical_mode"] = "Exact shape Fourier coefficients"
    compact = case.dimensions == 2 if compact is None else compact
    if compact:
        rcwa = _compact_solver(rcwa, torch)
        metadata["exterior_algebra"] = "even and odd layer coupling blocks"

    def layer_pixels(layer):
        if not layer.shapes:
            return layer.epsilon
        pixels = (shape_fourier_grid(layer, case, settings.grid, int(max(mx, my))) if exact_shapes else
                  raster(layer, case, settings.grid, midpoint=True))
        return torch.as_tensor(pixels, device=device)
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
        sim = rcwa(1/case.wavelength, [int(mx), int(my)], case.period,
                   dtype=torch.complex128, device=device)
        # Replace the released constructor's truncated pi in the propagation phase.
        sim.omega = 2*np.pi/case.wavelength
        metadata["wavenumber"] = "full-precision 2*pi/lambda"
        sim.add_input_layer(eps=case.incident)
        sim.add_output_layer(eps=case.exit)
        if compact and case.incident == 1:
            del sim.Sin
        if compact and case.exit == 1:
            del sim.Sout
        sim.set_incident_angle(*np.deg2rad([case.theta, case.phi]))
        if (compact and case.layers) or len(case.layers) > 1:
            _exterior_matrix(sim, case, layer_pixels, compact=compact)
        else:
            for layer in case.layers:
                sim.add_layer(layer.thickness, eps=layer_pixels(layer))
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
