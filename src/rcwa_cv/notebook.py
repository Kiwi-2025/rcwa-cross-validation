"""Shared sweep and display helpers for the case notebooks."""
import yaml
from threadpoolctl import threadpool_limits

from .case_loader import ROOT, load_case, points, resolve
from .reporting.plots import diagnostic_figures, spectral_figures
from .reporting.tables import POWER_METRICS, markdown_table, pretty, reference_differences
from .runner import configure, software_versions
from .validation.convergence import settings_series


def case_setup(case_path):
    """Load the same quick points and base settings used by the CLI."""
    configure()
    case = load_case(case_path)
    profile = yaml.safe_load((ROOT/"configs/quick.yaml").read_text(encoding="utf-8"))
    settings = settings_series(case, profile, "meent")[0][1]
    selected = list(points(case, "quick"))
    samples = [resolve(case, variant, overrides, settings) for variant, overrides in selected]
    meta = {"case":case["id"], "title":case["title"], "points":[
        {"variant":sample.variant, "wavelength_nm":sample.wavelength, "theta_deg":sample.theta,
         "phi_deg":sample.phi, **overrides} for sample, (_, overrides) in zip(samples, selected, strict=True)]}
    return samples, settings, meta


def solve_sweep(solve, samples, settings):
    """Run the supplied solver adapter at every selected point."""
    with threadpool_limits(limits=1, user_api="blas"):
        return {index:solve(point, settings) for index,point in enumerate(samples)}


def show_results(meta, results):
    from IPython.display import Markdown, display
    import matplotlib.pyplot as plt

    rows = []
    for name, samples in reference_differences(results):
        metrics = list(samples.values())
        if metrics:
            rows.append([name, len(samples),
                         pretty(max(row[k] for row in metrics for k in POWER_METRICS)),
                         pretty(max(row["max_amplitude"] for row in metrics))])
    if rows:
        display(Markdown(markdown_table(
            ("Solver vs Lumerical", "Matched points", "Max absolute power difference", "Max complex-amplitude difference"), rows)))
    else:
        display(Markdown("Comparison requires a Lumerical result and an open-source result at a common point."))
    for _, fig in spectral_figures(meta, results)+diagnostic_figures(meta, results):
        display(fig)
        plt.close(fig)


def show_versions(results):
    from IPython.display import Markdown, display

    versions = software_versions()
    if results.get("lumerical"):
        info = next(iter(results["lumerical"].values())).metadata
        versions["Lumerical RCWA"] = f"{info['version']} / build {info['build']}"
    if results.get("torcwa"):
        info = next(iter(results["torcwa"].values())).metadata
        versions["torcwa device"] = info["gpu"]
        versions["CUDA runtime"] = info["cuda"]
    display(Markdown(markdown_table(("Software or runtime", "Version or device"), list(versions.items()))))
