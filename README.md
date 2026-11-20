# RCWA Cross-Validation

A reproducible comparison of meent, torcwa on CUDA, grcwa, and Lumerical RCWA across 16 optical cases.

| Start here | Contents |
| --- | --- |
| [Benchmark report](BENCHMARK_REPORT.md) | All solver comparisons, figures, software versions, and the conclusion |
| [Periodic-case diagnosis](PERIODIC_DIAGNOSIS.md) | Controlled experiments on the twelve periodic discrepancies |
| [Case catalog](cases/README.md) | Physical scenarios, possible applications, notebooks, and Lumerical models |
| [Numerical dataset](results/benchmark.json) | Point coordinates, normalized powers and complex amplitudes, settings, and comparison metrics |
| [Comparison conventions](docs/conventions.md) | Polarization, reference planes, tolerances, and convergence criteria |

## Run the benchmark

On Windows, install [uv](https://docs.astral.sh/uv/), use a compatible NVIDIA driver, and install and license Ansys Lumerical FDTD. Run the setup once and then run the benchmark from the repository root:

```powershell
& .\scripts\setup_windows.ps1
& .\.venv\Scripts\rcwa-cv.exe benchmark
```

The default quick profile runs all cases and refreshes the dataset, figures, and root report after all four solvers complete. Use `rcwa-cv benchmark --profile convergence` for a full refinement sweep. The setup installs CUDA PyTorch and Jupyter in the project environment. For a nonstandard Lumerical installation, set `lumapi_path` in `configs/local.yaml` using [the example](configs/local.example.yaml). Reproduce the periodic-case controls using the command in [the diagnosis](PERIODIC_DIAGNOSIS.md#reproduce).

## Explore or reproduce a single case

Each case contains `case.yaml`, a Jupyter notebook, and Lumerical `model.fsp` and `model.lsf` files. The notebook starts with its mathematical model, physical scenario, and possible applications. The code cells rerun the solvers and draw plots inline. Open the native model to inspect the first quick-sweep point. Run the reconstruction script in a **new unsaved FDTD document** because it clears the current layout.

```powershell
& .\.venv\Scripts\jupyter-lab.exe
& .\.venv\Scripts\rcwa-cv.exe run B/B01
& .\.venv\Scripts\rcwa-cv.exe converge C/C02 --profile pilot --representative
& .\.venv\Scripts\rcwa-cv.exe report --run <run_id>
& .\.venv\Scripts\python.exe -m pytest -q
```

Individual runs, temporary files, and manually exported Lumerical scripts use the local `.runs/` directory. A complete benchmark publishes one JSON data document and a set of figures under `results/`. The report links to those figures.

To export a different sweep point or add a manually computed point to an individual run, use the same zero-based index:

```powershell
& .\.venv\Scripts\rcwa-cv.exe export-lumerical C/C02 --point 2
& .\.venv\Scripts\rcwa-cv.exe import-lumerical --run <run_id> --point 2 --mat <path-to-rcwa_output.mat>
```
