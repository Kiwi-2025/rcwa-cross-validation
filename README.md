# RCWA Cross-Validation

Compare five implementations of rigorous coupled-wave analysis on 16 optical benchmarks. The primary outputs are total reflectance, transmittance and absorptance, order efficiency, and complex power-normalized scattering amplitudes. Timing and device information accompany each run.

| Category | Benchmarks | Consistency |
| --- | --- | --- |
| A · Interfaces and thin films | [A01–A04](cases/A/) | [Category A results](results/A/consistency.md) |
| B · One-dimensional gratings | [B01–B06](cases/B/) | [Category B results](results/B/consistency.md) |
| C · Two-dimensional periodic structures | [C01–C06](cases/C/) | [Category C results](results/C/consistency.md) |

## Get started on Windows

Use Python 3.11 or 3.12, [uv](https://docs.astral.sh/uv/), and a compatible NVIDIA driver. From the repository root:

```powershell
uv sync --locked --extra cuda
uv run --no-sync rcwa-cv doctor
uv run --no-sync rcwa-cv run A/A01 --profile quick
uv run --no-sync rcwa-cv run all --representative
```

| Solver | Setup |
| --- | --- |
| meent, grcwa | Installed by the base Python environment |
| torcwa | Installed by the CUDA extra, with PyTorch CUDA 12.8. The adapter requires CUDA and uses float64 geometry, complex128 arithmetic, and disabled TF32 |
| S4 | Build inside Ubuntu 24.04 on WSL using the commands below |
| Lumerical RCWA | Install and license Lumerical FDTD. The runner finds a standard installation or accepts the full path via `LUMAPI_PATH` |

Install the S4 build dependencies in Ubuntu, then run the setup script from the checkout:

```bash
sudo apt install build-essential git python3-dev python3-numpy libopenblas-dev libfftw3-dev libboost-serialization-dev
bash scripts/setup_s4_wsl.sh
```

Copy `configs/local.example.yaml` to `configs/local.yaml` to override local paths or the GPU and WSL distribution. S4 uses the pinned Python-compatible [S4 fork](https://github.com/phoebe-p/S4/tree/9569f5e555b967a4324eb1ea593d0f9f40761a61). The Python GPU extra is optional if you select other solvers explicitly.

## Run and inspect a benchmark

```powershell
uv run --no-sync rcwa-cv list
uv run --no-sync rcwa-cv run B --solvers meent,torcwa,grcwa,s4,lumerical
uv run --no-sync rcwa-cv converge C/C02 --profile pilot --representative
uv run --no-sync rcwa-cv converge C/C02
uv run --no-sync rcwa-cv report --run <run_id>
uv run --no-sync rcwa-cv converge C/C02 --profile pilot --representative --resume <run_id>
```

`quick` uses a small sweep. `--representative` evaluates one nominal setting. The convergence profile independently varies the Fourier truncation, raster size and vertical slice count where applicable and uses the complete sweep by default. Use `--profile pilot` for a smaller refinement grid. A complete C02 convergence sweep can be expensive. Select solvers with `--solvers`.

One `case.yaml` per case defines the materials, geometry and excitation. Outputs go to `results/<category>/<case>/<run_id>/`, which contains the manifest, normalized arrays, settings, pairwise Markdown and CSV tables, and an HTML report. The top-level consistency tables summarize run coverage and errors. The project stores small tables in Git and generates per-run artifacts locally.

For the coordinate, polarization, reference plane, and consistency definitions, see [the comparison conventions](docs/conventions.md).

## Lumerical scripts

The runner builds each point with the modern RCWA simulation object and reads its native diffraction power, complex scattering amplitudes and total energy. Use the same script generator to export a point for manual execution:

```powershell
uv run --no-sync rcwa-cv export-lumerical A/A02 --point 2
```

The [checked-in Lumerical examples](scripts/lumerical/) cover A01, A02, B01 and C02. The export command supports every benchmark.

Open the generated `.lsf` in the script editor of a **new, unsaved FDTD document**. The script clears the current layout, builds and runs RCWA, and saves `rcwa_output.mat` in Lumerical's current working directory. [Ansys RCWA solver documentation](https://optics.ansys.com/hc/en-us/articles/12959229278611-RCWA-Solver-Simulation-Object)

To add a manually exported point to an existing comparison run, use the same case, point and numerical profile. The point index is zero-based.

```powershell
uv run --no-sync rcwa-cv import-lumerical --run <run_id> --point 2 --mat <path-to-rcwa_output.mat>
```
