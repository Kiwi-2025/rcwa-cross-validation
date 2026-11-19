from itertools import combinations

import numpy as np

from ..case_loader import load_case, resolve
from ..geometry import raster
from ..models import Layer, SolverSettings
from ..validation.compare import differences


def spectral_figures(manifest, results):
    import matplotlib.pyplot as plt

    variants = sorted({point["variant"] for point in manifest["points"]})
    figures = []
    for v, variant in enumerate(variants):
        fig, axes = plt.subplots(2, 2, figsize=(10, 6), constrained_layout=True)
        xkeys = ("normalized_frequency", "radius_nm", "rotation_deg", "theta_deg", "wavelength_nm")
        group = [p for p in manifest["points"] if p["variant"]==variant]
        key = next((k for k in xkeys if len({p.get(k) for p in group}) > 1), "wavelength_nm")
        present = False
        for name, data in results.items():
            entries = [(manifest["points"][index][key], result)
                       for index, result in data.items() if manifest["points"][index]["variant"]==variant]
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
            figures.append((f"spectrum-{v}.png", fig))
        else:
            plt.close(fig)
    return figures


def diagnostic_figures(manifest, results):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    output = []
    names = [name for name, data in results.items() if data]
    comparisons = [(left, right, [differences(results[left][i], results[right][i])
                                  for i in results[left].keys() & results[right].keys()])
                   for left, right in combinations(names, 2)]
    if any(samples for _, _, samples in comparisons):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.7), constrained_layout=True)
        for ax, metrics, title in zip(axes, (("max_R","max_T","max_A","max_order_power"), ("max_amplitude",)),
                                      ("Max absolute power difference", "Max complex-amplitude difference"), strict=True):
            matrix = np.full((len(names), len(names)), np.nan)
            for left, right, samples in comparisons:
                if samples:
                    i, j = names.index(left), names.index(right)
                    matrix[i,j] = matrix[j,i] = max(sample[m] for sample in samples for m in metrics)
            color = ax.imshow(np.maximum(matrix, 1e-16), cmap="viridis", norm=LogNorm(vmin=1e-16,
                              vmax=max(1e-15, float(np.nanmax(matrix)))))
            ax.set(xticks=range(len(names)), yticks=range(len(names)), xticklabels=names, yticklabels=names,
                   title=title)
            ax.tick_params(axis="x", labelrotation=35)
            for i, j in zip(*np.where(np.isfinite(matrix)), strict=True):
                ax.text(j, i, f"{matrix[i,j]:.1e}", ha="center", va="center", color="white", fontsize=8,
                        bbox=dict(facecolor="#1b2435", alpha=.6, edgecolor="none", pad=2))
            fig.colorbar(color, ax=ax, shrink=.8)
        output.append(("solver-differences.png", fig))
    shared = set.intersection(*(set(results[name]) for name in names)) if names else set()
    if shared:
        ordered = sorted(shared)
        index = ordered[len(ordered)//2]
        powers = [dict() for _ in range(2)]
        for name in names:
            result = results[name][index]
            for port in range(2):
                powers[port][name] = {tuple(map(int, order)): result.power[port,j]
                                     for j,order in enumerate(result.orders) if result.propagating[port,j]}
        fig, axes = plt.subplots(2, 2, figsize=(10.8, 6.2), constrained_layout=True)
        for port, power in enumerate(powers):
            orders = sorted({order for values in power.values() for order in values})
            for pol, axis in enumerate(axes[port]):
                axis.set(title=f"{('Reflection','Transmission')[port]} · {'sp'[pol]} input",
                         ylabel="Efficiency", xlabel="Diffraction order (m, n)")
                if not orders:
                    axis.text(.5, .5, "No propagating orders", ha="center", transform=axis.transAxes)
                    continue
                shown = sorted(sorted(orders, key=lambda order: max(
                    values.get(order, (0.,0.))[pol] for values in power.values()), reverse=True)[:11])
                x = np.arange(len(shown))
                width = .82/len(names)
                for k, name in enumerate(names):
                    values = [power[name].get(order, (0.,0.))[pol] for order in shown]
                    axis.bar(x+(k-(len(names)-1)/2)*width, values, width, label=name)
                axis.set_xticks(x, [str(order) for order in shown], rotation=30)
        point = manifest["points"][index]
        fig.suptitle(f"{manifest['case']} · {point['variant']} · {point['wavelength_nm']:.5g} nm · "
                     f"θ = {point['theta_deg']:g}°")
        if axes[0,0].containers:
            axes[0,0].legend(fontsize=8)
        output.append(("diffraction-orders.png", fig))
    return output


def geometry_figure(path):
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    spec = load_case(path)
    case = resolve(spec, "nominal", {}, SolverSettings(3, 128, 8))
    layers = list(case.layers)
    px, py = case.period
    backdrop = max(case.thickness*.10, min(px, py)*.2)
    stack = [Layer(backdrop, complex(case.incident)), *layers, Layer(backdrop, complex(case.exit))]
    x = np.linspace(-px/2, px/2, 129)
    z = np.r_[-backdrop, -backdrop + np.cumsum([layer.thickness for layer in stack])]
    # Rasterization starts at x=y=0. Roll the data so the displayed cell starts at -P/2.
    grids = [np.fft.fftshift(raster(layer, case, 128, midpoint=True)).real for layer in stack]
    cross = np.stack([grid[:, grid.shape[1]//2] for grid in grids])
    norm = Normalize(min(float(grid.min()) for grid in grids), max(float(grid.max()) for grid in grids))
    fig, axes = plt.subplots(1, 2 if case.dimensions==2 else 1, figsize=(8.8, 3.4), constrained_layout=True)
    ax = np.atleast_1d(axes)[0]
    image = ax.pcolormesh(x, z, cross, cmap="viridis", norm=norm, shading="flat")
    ax.invert_yaxis()
    ax.set(title="Cross-section at y ≈ 0", xlabel="x (nm)", ylabel="z (nm)")
    if case.dimensions==2:
        index = next((j for j,layer in enumerate(stack) if layer.shapes), 1)
        cut = axes[1]
        cut.imshow(grids[index].T, extent=(-px/2,px/2,-py/2,py/2), origin="lower",
                   aspect="equal", cmap="viridis", norm=norm)
        cut.set(title=f"Plan view of patterned layer {index}", xlabel="x (nm)", ylabel="y (nm)")
    fig.colorbar(image, ax=np.atleast_1d(axes).tolist(), label="Real relative permittivity")
    fig.suptitle(f"{case.id} · {spec['title']}")
    return fig


def save_figures(target, manifest, results, case_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures = [("geometry.png", geometry_figure(case_path))]
    figures += spectral_figures(manifest, results) + diagnostic_figures(manifest, results)
    target.mkdir(parents=True, exist_ok=True)
    for name, figure in figures:
        figure.savefig(target/name, dpi=125)
        plt.close(figure)
    return [target/name for name, _ in figures]
