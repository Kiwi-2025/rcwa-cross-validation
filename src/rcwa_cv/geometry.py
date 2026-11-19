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
    my = mx if case.dimensions == 2 else 0
    return np.array([(i, j) for i in range(-mx, mx + 1) for j in range(-my, my + 1)])


def midpoint_phase(orders, grid):
    """Translate FFT sample zero from the grid node to its pixel center."""
    return np.exp(-1j*np.pi*orders.sum(axis=1)/grid)
