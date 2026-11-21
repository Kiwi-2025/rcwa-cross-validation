import numpy as np


def raster(layer, case, size, midpoint=False):
    """Epsilon sampled over the periodic cell in (x, y) order."""
    nx, ny = size, size if case.dimensions == 2 else 1
    px, py = case.period
    offset = .5 if midpoint else 0
    x = (np.arange(nx)[:, None] + offset) * px / nx
    y = (np.arange(ny)[None, :] + offset) * py / ny
    epsilon = np.full((nx, ny), layer.epsilon, dtype=np.complex128)
    for shape in layer.shapes:
        cx, cy = shape.center
        xx = (x - cx + px/2) % px - px/2
        yy = (y - cy + py/2) % py - py/2
        if shape.kind == "circle":
            mask = np.hypot(xx, yy) < shape.width/2
        else:
            angle = np.deg2rad(shape.rotation)
            u = np.cos(angle)*xx + np.sin(angle)*yy
            v = -np.sin(angle)*xx + np.cos(angle)*yy
            half = shape.width/2
            boundary_tol = 1e-12 * px
            mask = (u >= -half - boundary_tol) & (u < half - boundary_tol)
            if case.dimensions == 2:
                mask &= (v >= -shape.length/2) & (v < shape.length/2)
        epsilon[mask] = shape.epsilon
    return epsilon


def rectangular_orders(case, settings):
    mx = settings.order if case.dimensions else 0
    my = (mx if settings.order_y is None else settings.order_y) if case.dimensions == 2 else 0
    return np.array([(i, j) for i in range(-mx, mx + 1) for j in range(-my, my + 1)])


def midpoint_phase(orders, grid):
    """Translate FFT sample zero from the grid node to its pixel center."""
    return np.exp(-1j*np.pi*orders.sum(axis=1)/grid)


def shape_fourier_grid(layer, case, size, half_order):
    """Encode the exact coefficients of disjoint periodic shapes for the solver FFT."""
    from scipy.special import j1

    bound = 2 * half_order
    if case.dimensions != 2 or size < 2 * bound + 1:
        raise ValueError("Exact shape coefficients require a de-aliased 2D grid.")
    indices = np.arange(-bound, bound + 1)
    px, py = case.period
    kx, ky = np.meshgrid(2 * np.pi * indices / px, 2 * np.pi * indices / py, indexing="ij")
    coefficients = np.zeros_like(kx, dtype=complex)
    coefficients[bound, bound] = layer.epsilon
    for shape in layer.shapes:
        if shape.kind == "circle":
            radius = shape.width / 2
            kr = radius * np.hypot(kx, ky)
            profile = np.ones_like(kr)
            np.divide(2 * j1(kr), kr, out=profile, where=kr != 0)
            area = np.pi * radius**2
        elif shape.kind == "rectangle":
            alpha = np.deg2rad(shape.rotation)
            u = np.cos(alpha) * kx + np.sin(alpha) * ky
            v = -np.sin(alpha) * kx + np.cos(alpha) * ky
            profile = np.sinc(u * shape.width / (2 * np.pi)) * np.sinc(v * shape.length / (2 * np.pi))
            area = shape.width * shape.length
        else:
            raise ValueError(f"No closed-form Fourier coefficients for {shape.kind}.")
        phase = np.exp(-1j * (kx * shape.center[0] + ky * shape.center[1]))
        coefficients += (shape.epsilon - layer.epsilon) * area / (px * py) * profile * phase

    spectrum = np.zeros((size, size), dtype=complex)
    midpoint = np.exp(1j * np.pi * (indices[:, None] + indices[None, :]) / size)
    spectrum[np.ix_(indices % size, indices % size)] = coefficients * midpoint
    return np.fft.ifft2(spectrum) * size**2
