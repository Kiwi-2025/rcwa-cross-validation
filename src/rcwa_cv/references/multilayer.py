import numpy as np

from ..conventions import incident_basis, result_from_xy


def solve(case, _settings):
    """Independent isotropic thin-film solution using scalar scattering recursion."""
    if case.dimensions:
        raise ValueError("The analytic reference applies only to planar cases.")
    transverse = case.incident * np.sin(np.deg2rad(case.theta))**2
    epsilon = np.array([case.incident, *(layer.epsilon for layer in case.layers), case.exit], complex)
    kz = np.sqrt(epsilon - transverse + 0j)
    phases = np.exp(2j*np.pi/case.wavelength*kz[1:-1]*[layer.thickness for layer in case.layers])
    basis, _ = incident_basis(case)
    fields = np.zeros((2, 1, 2, 2), complex)
    for pol, admittance in enumerate((kz, epsilon/kz)):
        r, t = 0j, 1+0j
        for j in reversed(range(len(epsilon)-1)):
            rj = (admittance[j] - admittance[j+1])/(admittance[j] + admittance[j+1])
            phase = phases[j] if j < len(phases) else 1
            denominator = 1 + rj*r*phase**2
            t *= (1+rj)*phase/denominator
            r = (rj+r*phase**2)/denominator
        fields[:, 0, :, pol] = np.array([r, t])[:, None]*basis[:2, pol]
    return result_from_xy(case, np.zeros((1, 2), int), fields,
                          {"version": "scalar scattering reference", "device": "CPU"})
