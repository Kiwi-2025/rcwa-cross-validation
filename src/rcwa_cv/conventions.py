import numpy as np

from .models import SimulationResult


CUTOFF_TOLERANCE = 1e-10


def wavevectors(case, orders):
    theta, phi = np.deg2rad([case.theta, case.phi])
    incident = np.sqrt(case.incident) * np.sin(theta) * np.array([np.cos(phi), np.sin(phi)])
    transverse = incident + orders * case.wavelength / np.array(case.period)
    kz2 = np.array([case.incident, case.exit])[:, None] - np.sum(transverse**2, axis=-1)
    return transverse, kz2


def basis(case, transverse, kz, n):
    """Return columns s and p=s cross k_hat, in global Cartesian coordinates."""
    transverse = np.asarray(transverse)
    phi = np.deg2rad(case.phi)
    azimuth = np.arctan2(transverse[1], transverse[0]) if np.linalg.norm(transverse) > 1e-12 else phi
    s = np.array([-np.sin(azimuth), np.cos(azimuth), 0.])
    p = np.cross(s, np.array([*transverse, kz])/n)
    return np.column_stack((s, p))


def incident_basis(case):
    transverse, kz2 = wavevectors(case, np.zeros((1, 2)))
    kz = np.sqrt(kz2[0, 0])
    return basis(case, transverse[0], kz, np.sqrt(case.incident)), kz


def result_from_xy(case, orders, tangential, metadata):
    """Project Cartesian E onto unit-power diffraction channels."""
    transverse, kz2 = wavevectors(case, orders)
    _, kzi = incident_basis(case)
    prop = kz2 > CUTOFF_TOLERANCE
    amplitude = np.zeros_like(tangential, dtype=complex)
    for port, eps in enumerate((case.incident, case.exit)):
        for i in np.flatnonzero(prop[port]):
            kz = np.sqrt(kz2[port, i])
            xy = basis(case, transverse[i], (-kz if port == 0 else kz), np.sqrt(eps))[:2]
            amplitude[port, i] = np.linalg.solve(xy, tangential[port, i]) * np.sqrt(kz/kzi)
    return result_from_amplitudes(case, orders, amplitude, metadata)


def result_from_amplitudes(case, orders, amplitude, metadata, power=None, totals=None):
    _, kz2 = wavevectors(case, orders)
    prop = kz2 > CUTOFF_TOLERANCE
    amplitude = np.where(prop[:, :, None, None], amplitude, 0)
    if power is None:
        power = np.sum(abs(amplitude)**2, axis=2)
    power = np.where(prop[:, :, None], power, 0)
    if totals is None:
        totals = power.sum(axis=1)
    return SimulationResult(orders, prop, power, amplitude, totals, metadata)
