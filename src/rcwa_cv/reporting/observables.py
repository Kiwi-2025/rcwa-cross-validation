"""Case-specific observables beyond the all-channel difference tables."""
from itertools import groupby

import numpy as np
from scipy.signal import find_peaks, peak_widths

from ..storage import load_result


COLUMNS = ("Solver", "Variant", "Point", "Observable", "Value", "Unit")


def collect(folder, manifest):
    case = manifest["case"]
    rows = []
    for solver, state in manifest["solvers"].items():
        spectrum = []
        for entry in state["completed"]:
            idx = entry["index"]
            point = manifest["points"][idx]
            result = load_result(folder/entry["path"])
            def row(name, value, unit="fraction"):
                rows.append([solver, point["variant"], idx, name, value, unit])
            if manifest["lossy"]:
                for i, pol in enumerate("sp"):
                    row(f"{pol} absorptance", 1-result.totals[:,i].sum())
            if case == "B05":
                hi, lo = sorted(result.totals[1])
                if lo > 0:
                    row("Transmission extinction ratio", 10*np.log10(hi/lo), "dB")
            if case == "C02" and "normalized_frequency" in point:
                spectrum.append((point["variant"], point["normalized_frequency"], float(result.totals[1,0])))
            if case in ("B06","C06"):
                for i, pol in enumerate("sp"):
                    for target in ([(-1,0)] if case == "B06" else [(1,0)]):
                        index = np.flatnonzero(np.all(result.orders==target,axis=1))
                        if len(index):
                            row(f"{pol} transmitted order {target}", result.power[1,index[0],i])
            if case == "C04":
                index = np.flatnonzero(np.all(result.orders==0,axis=1))
                if len(index):
                    jones = result.amplitude[1,index[0]]
                    circular = np.array([[1,1],[1j,-1j]])/np.sqrt(2)
                    response = circular.conj().T @ jones @ circular
                    row("Circular + to - conversion", abs(response[1,0])**2)
                    row("Circular - to + conversion", abs(response[0,1])**2)
        if case != "C02":
            continue
        for variant, grouped in groupby(sorted(spectrum), key=lambda x:x[0]):
            samples = list(grouped)
            if len(samples) < 25:
                continue
            _, x, transmission = zip(*samples)
            peaks, _ = find_peaks(transmission, prominence=.02)
            if not len(peaks):
                continue
            _, _, left, right = peak_widths(transmission, peaks)
            width = np.interp(right,np.arange(len(x)),x)-np.interp(left,np.arange(len(x)),x)
            for i, (idx, w) in enumerate(zip(peaks,width,strict=True),1):
                rows.extend([[solver,variant,"—",f"Peak {i} location",x[idx],"a/lambda"],
                             [solver,variant,"—",f"Peak {i} half-prominence width",w,"a/lambda"]])
    return rows
