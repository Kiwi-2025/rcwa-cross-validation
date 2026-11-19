import numpy as np


def checks(result, lossy):
    propagating_sum = result.power.sum(axis=1)
    from_amplitude = (abs(result.amplitude)**2).sum(axis=2)
    energy = result.totals.sum(axis=0)
    return {
        "order_sum_error": float(abs(propagating_sum-result.totals).max()),
        "amplitude_power_error": float(abs(from_amplitude-result.power).max()),
        "conservation_or_passivity_error": float(np.maximum(energy-1, 0).max() if lossy else abs(energy-1).max()),
        "negative_power": float(max(0, -result.power.min(), -result.totals.min())),
    }
