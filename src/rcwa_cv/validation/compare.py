import numpy as np


def differences(a, b):
    """Match by port, reciprocal-lattice order and polarization."""
    def channels(result, port):
        return {tuple(map(int, order)): i for i, order in enumerate(result.orders) if result.propagating[port, i]}

    values = dict(max_R=float(np.max(abs(a.totals[0]-b.totals[0]))),
                  max_T=float(np.max(abs(a.totals[1]-b.totals[1]))),
                  max_A=float(np.max(abs(a.totals.sum(axis=0)-b.totals.sum(axis=0)))),
                  max_order_power=0., max_amplitude=0., max_phase_deg=None,
                  complete=True, worst_amplitude_channel=None)
    for p in range(2):
        left, right = channels(a, p), channels(b, p)
        values["complete"] &= left.keys() == right.keys()
        for key in left.keys() & right.keys():
            i, j = left[key], right[key]
            numbers = abs(a.power[p,i]-b.power[p,j])
            values["max_order_power"] = max(values["max_order_power"], float(numbers.max()))
            f, g = a.amplitude[p,i], b.amplitude[p,j]
            delta = abs(f-g)
            if delta.max() > values["max_amplitude"]:
                values["max_amplitude"] = float(delta.max())
                po, pi = np.unravel_index(delta.argmax(), delta.shape)
                values["worst_amplitude_channel"] = f"{'RT'[p]}{key} {'sp'[pi]} to {'sp'[po]}"
            eligible = (abs(f)**2 >= 1e-4) & (abs(g)**2 >= 1e-4)
            if eligible.any():
                phase = float(abs(np.angle((f*g.conj())[eligible], deg=True)).max())
                values["max_phase_deg"] = max(values["max_phase_deg"] or 0., phase)
    return values


def meets(values, tolerance, phase_deg=.5):
    return (values["complete"] and
            max(values[k] for k in ("max_R","max_T","max_A","max_order_power","max_amplitude")) <= tolerance
            and (values["max_phase_deg"] or 0.) <= phase_deg)
