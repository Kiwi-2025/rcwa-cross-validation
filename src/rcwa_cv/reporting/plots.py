import numpy as np


def plot_spectra(folder, manifest):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ..storage import load_result

    variants = sorted({point["variant"] for point in manifest["points"]})
    figures = []
    for v, variant in enumerate(variants):
        fig, axes = plt.subplots(2, 2, figsize=(10, 6), constrained_layout=True)
        xkeys = ("normalized_frequency", "radius_nm", "rotation_deg", "theta_deg", "wavelength_nm")
        group = [p for p in manifest["points"] if p["variant"]==variant]
        key = next((k for k in xkeys if len({p.get(k) for p in group}) > 1), "wavelength_nm")
        present = False
        for name, state in manifest["solvers"].items():
            entries = [(manifest["points"][e["index"]][key], load_result(folder/e["path"]))
                       for e in state["completed"] if manifest["points"][e["index"]]["variant"]==variant]
            if not entries:
                continue
            present = True
            entries.sort(key=lambda entry: entry[0])
            x = [t for t, _ in entries]
            power = np.array([r.totals for _,r in entries])
            for i, pol in enumerate("sp"):
                line, = axes[0,i].plot(x, power[:,0,i], ".-", label=name)
                axes[0,i].plot(x, power[:,1,i], ":", color=line.get_color())
                phase = []
                for _, res in entries:
                    target = (1, 0) if manifest["case"]=="C06" else (0, 0)
                    found = np.flatnonzero(np.all(res.orders==target, axis=1))
                    a = res.amplitude[1, found[0], i, i] if len(found) else 0
                    phase.append(np.angle(a, deg=True) if abs(a)**2 >= 1e-4 else np.nan)
                axes[1,i].plot(x, phase, ".-", label=name)
                axes[0,i].set_title(f"{pol} input: reflection (solid), transmission (dotted)")
                axes[1,i].set(xlabel=key.replace("_"," "), ylabel="Co-polarized transmission phase (deg)")
                axes[0,i].set_ylabel("Power / incident power")
        if present:
            axes[0,0].legend()
            fig.suptitle(f"{manifest['case']} · {manifest['title']} · {variant}")
            filename = f"figures/variant-{v}.png"
            (folder/"figures").mkdir(exist_ok=True)
            fig.savefig(folder/filename, dpi=150)
            figures.append(filename)
        plt.close(fig)
    return figures
