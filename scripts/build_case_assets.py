"""Create editable notebooks and native Lumerical projects from the case catalog."""
from argparse import ArgumentParser
import json

import yaml

from rcwa_cv.case_loader import ROOT, catalog, load_case, points, resolve
from rcwa_cv.runner import configure
from rcwa_cv.solvers import lumerical
from rcwa_cv.validation.convergence import settings_series


def make_notebook(case):
    case_id = case["id"]
    cells = []

    def add(kind, source):
        cell = {"cell_type":kind, "id":f"cell-{len(cells)}", "metadata":{},
                "source":source.strip().splitlines(keepends=True)}
        if kind=="code":
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)

    add("markdown", f"""# {case_id} · {case["title"]}

{case["description"]}

Run the solver cells separately or use **Run All** with the project environment. Each cell uses the same
geometry, excitation and quick sweep as the CLI. The native [Lumerical model](model.fsp) and
[reconstruction script](model.lsf) represent quick-sweep point 0. See the [case page](README.md)
for the published figures and [case.yaml](case.yaml) for the numerical inputs.""")
    add("markdown", """## Saved quick-sweep preview

![Reflection, transmission and phase](figures/spectrum-0.png)

![Pairwise solver differences](figures/solver-differences.png)""")
    add("code", f"""from IPython.display import display
import matplotlib.pyplot as plt

from rcwa_cv.case_loader import catalog
from rcwa_cv.notebook import case_setup, show_results, show_versions, solve_sweep
from rcwa_cv.reporting.plots import geometry_figure

case_path = catalog("{case_id}")[0]
samples, settings, metadata = case_setup(case_path)
results = {{}}

print(f"{{len(samples)}} points, Fourier truncation index {{settings.order}}")
figure = geometry_figure(case_path)
display(figure)
plt.close(figure)""")
    if not case["periodic_dimensions"]:
        add("markdown", "## Analytic multilayer reference")
        add("code", """from rcwa_cv.references.multilayer import solve as solve_reference

results["reference"] = solve_sweep(solve_reference, samples, settings)""")
    for name, title, module in (
        ("meent", "meent · NumPy CPU", "meent_cpu"),
        ("torcwa", "torcwa · CUDA GPU, complex128", "torcwa_cuda"),
        ("grcwa", "grcwa · NumPy CPU", "grcwa_cpu"),
    ):
        add("markdown", f"## {title}")
        add("code", f"""from rcwa_cv.solvers.{module} import probe, solve

print(probe())
results["{name}"] = solve_sweep(solve, samples, settings)""")
    add("markdown", """## Lumerical RCWA

This cell uses the installed, licensed FDTD application through its Python API. It reuses one session
across the sweep and evaluates the same model generator used by the reconstruction script.""")
    add("code", """from rcwa_cv.solvers.lumerical import session, solve

with session() as fdtd:
    print(f"Lumerical build {fdtd.version()}")
    results["lumerical"] = solve_sweep(solve, samples, settings)""")
    add("markdown", """## Compare the solvers

The spectra show total reflection, transmission and the co-polarized transmission phase.
The order plot uses a point shared by the solvers. The heatmaps show maximum discrepancies
over the tested points. Periodic quick sweeps provide preliminary comparisons.""")
    add("code", """show_versions(results)
show_results(metadata, results)""")
    return {"cells":cells, "metadata":{"kernelspec":{"display_name":"Python 3",
            "language":"python","name":"python3"},"language_info":{"name":"python"}},
            "nbformat":4, "nbformat_minor":5}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("selection", default="all", nargs="?")
    parser.add_argument("--skip-native", action="store_true", help="Generate notebooks and scripts without launching Lumerical.")
    args = parser.parse_args()
    configure()
    quick = yaml.safe_load((ROOT/"configs/quick.yaml").read_text(encoding="utf-8"))
    models = []
    for path in catalog(args.selection):
        case = load_case(path)
        notebook = make_notebook(case)
        (path.parent/f"{case['id']}.ipynb").write_text(
            json.dumps(notebook, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
        variant, parameters = next(points(case,"quick"))
        settings = settings_series(case,quick,"lumerical")[0][1]
        model = resolve(case, variant, parameters, settings)
        (path.parent/"model.lsf").write_text(
            lumerical.build_script(model,settings,"rcwa_output.mat"), encoding="utf-8")
        models.append((path.parent/"model.fsp", model, settings))
    if not args.skip_native:
        with lumerical.session() as fdtd:
            for target, model, settings in models:
                fdtd.eval(lumerical.build_script(model, settings, model_only=True))
                fdtd.save(str(target))
                print(f"Saved {target.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
