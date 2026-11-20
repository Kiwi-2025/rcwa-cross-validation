# Why the Twelve Periodic Cases Disagree

[Benchmark tables and figures](BENCHMARK_REPORT.md) · [Numerical data](results/benchmark.json) · [Diagnostic script](scripts/diagnose_periodic.py)

At the selected points, the native Meent material convolution matrices account for most of its difference from grcwa in eleven cases. Replacing those matrices with the same discrete operator as grcwa reduces the maximum complex-amplitude difference to $1.27\times10^{-12}$ across all twelve points. The main B06 discrepancy is a lateral Lumerical phase offset that tracks half a native mesh interval.

The diagnostic runs used Meent 0.13.2, grcwa 0.1.2, torcwa 0.1.4.2 on an NVIDIA GeForce RTX 4060 Laptop GPU with PyTorch 2.8.0+cu128, and Lumerical v252, build 8.34.4175. The original quick sweep supplies the worst-gap point for each case. The operator, grid, slice, and basis controls are new runs.

## Matched material operators

For each case, the test uses the quick benchmark point with the largest pairwise complex-amplitude difference. The quick runs use a one-dimensional Fourier half-order $M=8$ and a grid of $N=128$ for class B. Class C uses $M=3$ on each axis and a $96\times96$ grid. At these settings grcwa and torcwa agree across the full periodic quick sweep to within $1.08\times10^{-11}$ in complex amplitude.

The experiment holds the permittivity raster, retained Fourier orders, Meent eigensolver, source, and output conversion fixed. **Native** uses Meent's continuous Fourier coefficients with directional inverse factorization. **Direct CFS** uses the direct permittivity product in both transverse directions and computes the continuous coefficients of the same piecewise-constant raster. **Direct DFS** uses the same direct product with the centered discrete Fourier coefficients used by grcwa. The first substitution isolates the directional factorization. The second measures the remaining effect of integrating the pixels versus sampling them at their centers. Fourier factorization changes how a finite expansion represents products at interfaces, especially where the permittivity jumps. [Li, *JOSA A* 13, 1870–1876](https://doi.org/10.1364/JOSAA.13.001870)

All four numerical columns below report the maximum absolute difference in a power-normalized complex amplitude relative to grcwa at the same settings. **Finer native** uses $(M,N)=(32,512)$ for class B and $(6,384)$ for class C. B05 uses $M=48$. B04 uses 32 vertical slices instead of 8.

| Case | Selected excitation | Native | Direct CFS | Direct DFS | Finer native |
| --- | --- | ---: | ---: | ---: | ---: |
| [B01](#b01) | 620 nm | 0.02627 | 3.41e-4 | 9.93e-14 | 0.006428 |
| [B02](#b02) | 1200 nm | 0.1468 | 0.002231 | 1.99e-14 | 0.03901 |
| [B03](#b03) | 920 nm, θ = 30°, φ = 45° | 0.01130 | 1.59e-4 | 6.08e-15 | 0.002838 |
| [B04](#b04) | 620 nm | 0.01522 | 1.83e-4 | 1.79e-14 | 0.003941 |
| [B05](#b05) | 1200 nm | 0.2027 | 0.008124 | 3.77e-13 | 0.01001 |
| [B06](#b06) | 633 nm, θ = 12° | 8.66e-5 | 8.66e-5 | 2.43e-13 | 5.41e-6 |
| [C01](#c01) | 1220 nm | 0.1166 | 0.001665 | 1.91e-15 | 0.08062 |
| [C02](#c02) | $P/\lambda_0=0.526$ | 1.017 | 0.01725 | 2.24e-13 | 0.8738 |
| [C03](#c03) | 633 nm, radius 90 nm | 0.2659 | 5.39e-4 | 1.58e-13 | 0.1330 |
| [C04](#c04) | 633 nm, rotation 45° | 0.3451 | 0.02613 | 1.27e-12 | 0.2669 |
| [C05](#c05) | 1200 nm, lateral shift 350 nm | 0.1233 | 3.34e-4 | 1.02e-13 | 0.06581 |
| [C06](#c06) | 1420 nm | 1.209 | 0.01584 | 1.33e-13 | 0.5861 |

## Sensitivity to order and grid

The CPU columns give the largest change in complex amplitude within either native Meent or grcwa between the quick run and a one-axis refinement. The Lumerical columns give the same sensitivity within Lumerical using the published profile's settings. The order test raises only nominal $M$ to 12 for class B or 4 for class C. The grid test raises only $N$ to 256 or 192, respectively. A size comparison applies to these specific increments and points. Lumerical builds the permittivity profile from CAD geometry, and the open-source adapters use shared midpoint samples. [Ansys RCWA simulation object](https://optics.ansys.com/hc/en-us/articles/12959229278611-RCWA-Solver-Simulation-Object)

| Case | CPU order | CPU grid | Lumerical order | Lumerical grid |
| --- | ---: | ---: | ---: | ---: |
| B01 | 0.008561 | 2.56e-4 | 0.006359 | 0.007830 |
| B02 | 0.04774 | 0.001674 | 0.02324 | 0.002771 |
| B03 | 0.003638 | 1.20e-4 | 0.005395 | 0.007046 |
| B04 | 0.003801 | 0.002123 | 0.005095 | 0.006311 |
| B05 | 0.1221 | 0.005827 | 0.01902 | 0.001862 |
| B06 | 2.03e-12 | 6.50e-5 | 0.006258 | 0.009177 |
| C01 | 0.1088 | 0.02739 | 0.03768 | 0.007866 |
| C02 | 0.2537 | 0.1023 | 0.1213 | 0.02781 |
| C03 | 0.07184 | 9.84e-4 | 0.01941 | 0.001091 |
| C04 | 0.1076 | 0.2982 | 0.01566 | 0.006266 |
| C05 | 0.02932 | 0.02015 | 0.01114 | 3.56e-4 |
| C06 | 0.6559 | 0.05002 | 0.04300 | 0.01648 |

## Lumerical Fourier basis

On the installed v252 build, the rectangular `max number ku` and `max number kv` settings control the reported Fourier **half-orders**. The published adapter supplied $2M+1$ on patterned axes, so its quick 2D basis was $15\times15$, while the open-source basis was $7\times7$. The 1D open-source runs retained 17 x modes. Lumerical retained 35 x modes and three y sectors, with an active central y sector for the y-invariant gratings. The matched control requests $M$ on the patterned axes and checks the actual bounds of the returned order list. Lumerical's minimum y half-order is 1. A uniform y profile keeps the extra y sectors decoupled, including under conical incidence. The control uses the same CAD geometry and mesh as the published quick profile.

| Case | Published Lumerical basis vs grcwa | Matched Lumerical basis vs grcwa |
| --- | ---: | ---: |
| B01 | 0.02067 | 0.01724 |
| B02 | 0.07398 | 2.04e-13 |
| B03 | 0.01360 | 0.01610 |
| B04 | 0.01526 | 0.01597 |
| B05 | 0.1797 | 4.02e-13 |
| B06 | 0.01956 | 0.02077 |
| C01 | 0.05238 | 0.007552 |
| C02 | 0.4638 | 0.05883 |
| C03 | 0.1403 | 0.002191 |
| C04 | 0.4680 | 0.4436 |
| C05 | 0.07044 | 0.01492 |
| C06 | 0.8240 | 0.1941 |

The columns give maximum absolute complex-amplitude differences at the selected points. Matching the order explains the entire selected Lumerical–grcwa gap in B02 and B05 and most of it in C01, C02, C03, C05, and C06. The remaining cases need the geometry and phase controls documented below. The published benchmark tables retain their original numerical settings. The matched controls and their native order counts are available in the diagnostic data.

## Case findings

### B01

The largest difference occurs in zeroth-order p transmission. At this rectangular dielectric interface the open-source order change is about 33 times the grid change. After shifting the whole grating by one quarter period and removing the predicted translation phase $e^{-i2\pi m\Delta x/P_x}$, all four solvers recover their original amplitudes to within $1.82\times10^{-13}$. This checks the lateral phase conversion for the translated grating.

### B02

The high-index step strongly affects p reflection. The open-source order-only change is about 29 times the grid-only change. Holding the raster and order fixed, the directional factorization accounts for most of the native Meent difference. Matching the actual Lumerical order gives agreement with grcwa to round-off at this excitation. The finer Meent–grcwa gap of 0.0390 still exceeds the benchmark tolerance.

### B03

Oblique incidence at nonzero azimuth couples the two polarizations. The selected disagreement occurs in the $(+1,0)$ transmitted s channel. Matching the operator reduces it to round-off at that excitation, including the cross-polarized channels in the comparison. The order change dominates the grid change.

### B04

The trapezoidal cross section introduces vertical staircasing in addition to transverse sampling and Fourier truncation. Increasing the slice count from 8 to 32 at fixed $M=12, N=256$ changes the complex amplitudes by up to 0.00427 within the CPU solvers and 0.00360 within Lumerical. These are comparable to the order-only changes. The matched-operator control attributes the main Meent–grcwa gap at eight slices to factorization.

### B05

The metallic wire grid has its largest disagreement in p transmission. At 1200 nm the published p transmittances are 0.868 (Meent), 0.600 (grcwa and torcwa), and 0.849 (Lumerical). The matched-order Lumerical run gives 0.600, identifying Fourier truncation as the source of the Lumerical–grcwa gap at this point. The open-source order refinement changes amplitudes by 0.122, compared with 0.00583 from grid refinement. The native Meent–grcwa gap falls from 0.203 to 0.0100 at $M=48$. The slow order sensitivity is consistent with established TM convergence behavior at metallic grating interfaces. [Lalanne and Morris, *JOSA A* 13, 779–784](https://doi.org/10.1364/JOSAA.13.000779)

### B06

The weak sinusoidal modulation agrees in power. Across all seven quick-sweep angles, the largest four-solver power difference is $1.70\times10^{-4}$. The Lumerical/grcwa phase difference is approximately $+1.3245^\circ m$, with a power-weighted RMS residual of $0.00468^\circ$ in channels with power at least $10^{-4}$ in both solvers. For a 1000 nm period that phase ramp is equivalent to an apparent shift of $-3.679$ nm under the common phase convention. Removing the fitted ramp for diagnosis lowers the maximum amplitude difference from 0.01956 to $1.63\times10^{-4}$.

The new runs at 12° held the 128 CAD index strips fixed and varied only the Lumerical x-mesh setting. The reported material's first Fourier harmonic has phase within 0.0004° of zero when evaluated at its reported sample centers. The phase inferred from the diffracted fields follows half the actual mesh step to within 0.001° per order. This locates the dominant discrepancy in the effective lateral phase origin of the sampled fields. [Ansys RCWA index result](https://optics.ansys.com/hc/en-us/articles/12959229278611-RCWA-Solver-Simulation-Object)

| Requested x mesh | Reported x samples | Fitted degrees per order | Half-step prediction | Max amplitude difference after fit |
| ---: | ---: | ---: | ---: | ---: |
| 64 | 136 | 1.324519° | 1.323529° | 1.63e-4 |
| 128 | 136 | 1.324519° | 1.323529° | 1.63e-4 |
| 256 | 256 | 0.703399° | 0.703125° | 6.50e-5 |
| 512 | 512 | 0.351905° | 0.351563° | 8.12e-5 |

### C01

The square hole array at normal incidence has fourfold symmetry, which requires equal total power for s and p incidence. At 1220 nm native Meent gives transmittances of 0.2725 and 0.0558. The other three engines each produce equal s and p transmittance to numerical precision. The native Meent power split decreases from 0.2167 to 0.0601 at the finer setting. The operator controls and the large order sensitivity identify a finite-order directional factorization effect in the tested Meent solution.

The native material matrices provide a direct check for C01, C02, and C03. Each raster is invariant under exchanging x and y. If $S$ permutes the Fourier modes by $(m,n)\mapsto(n,m)$, the transverse material operators should satisfy $C_x=S C_y S^\mathrm{T}$. The native operators use successive one-dimensional Fourier operations and matrix inversions. They give relative maximum-element residuals of 23.8%, 7.27%, and 5.47%, respectively, at quick order. The native longitudinal operators satisfy the corresponding exchange check to within $2.1\times10^{-15}$. This localizes the polarization asymmetry to the finite transverse material operators.

### C02

The narrow guided resonance shifts with the material operator and Fourier resolution. At $P/\lambda_0=0.526$, quick transmittance is 0.312 for grcwa and torcwa and 0.771 for Lumerical. Meent gives 0.678 for s and 0.843 for p, even though the square slab requires equal total power for the two inputs at normal incidence. The 49-point local sweep resolves the following dominant sampled peaks. The table and figure use the actual Fourier half-order $M$ per axis.

| Solver | $M$ | $N$ | s peak $P/\lambda_0$ | p peak $P/\lambda_0$ | T at 0.526 (s, p) |
| --- | ---: | ---: | ---: | ---: | --- |
| grcwa | 3 | 96 | 0.5235 | 0.5235 | 0.312, 0.312 |
| Meent | 3 | 96 | 0.5315 | 0.5250 | 0.678, 0.843 |
| grcwa | 6 | 384 | 0.5245 | 0.5245 | 0.754, 0.754 |
| Meent | 6 | 384 | 0.5295 | 0.5260 | 0.761, 0.994 |
| Lumerical | 7 | 96 | 0.5245 | 0.5245 | 0.771, 0.771 |
| Lumerical | 9 | 192 | 0.5250 | 0.5250 | 0.883, 0.883 |

The native Meent peak split shrinks from 0.0065 to 0.0035 across these settings. A shift of just 0.0010 moves the grcwa transmission at the benchmark frequency by 0.442. The common operator collapses the amplitude discrepancy at the same frequency, and the spectra show how a finite-basis shift amplifies that sensitivity in the original comparison. These sampled peak locations carry a frequency step of 0.0005. Further refinement is needed to establish converged peaks. [Ansys photonic crystal slab example](https://optics.ansys.com/hc/en-us/articles/4416343906067-Photonic-Crystal-Slab-RCWA)

Matching Lumerical and grcwa at actual $M=3$ brings the Lumerical transmittance at 0.526 to 0.259 and reduces their maximum amplitude difference from 0.464 to 0.0588. The mismatch in retained orders therefore contributes substantially to the published intersolver result at this frequency.

![C02 local guided resonance for the two incident polarizations at the quick and finer numerical settings](results/figures/C02/resonance-diagnosis.png)

### C03

At the 90 nm radius, complex transmission is sensitive to the lateral Fourier truncation. The order-only change is about 73 times the grid-only change, and the native gap remains 0.133 at the finer setting. The same-operator control agrees to round-off. The native Meent also shows a total-power polarization split of $2.84\times10^{-3}$ in this fourfold-symmetric cell, so comparing powers alone understates the error in the meta-atom's complex response.

### C04

The 45° nanofin gives the largest selected discrepancy in the s-to-p transmitted amplitude. Grid refinement changes the open-source result by 0.298, almost three times the order-only change. Even with the direct CFS operator, the residual gap of 0.0261 is the largest of the twelve CFS controls. Both rotated-edge sampling and directional factorization contribute. The native Meent–grcwa gap rises from 0.345 to 0.399 on the intermediate combined refinement and then falls to 0.267.

At 45°, the matched-order Lumerical–grcwa difference drops from 0.4436 to 0.08308 when both the order and grid are refined. At 22.5° and 67.5° the corresponding finer gap is $3.49\times10^{-4}$. Reversing Lumerical's angle reverses the cross-polarized amplitude and raises the 45° finer gap to 1.223. The positive-angle control confirms that both adapters model the same rotation direction.

### C05

At the half-period layer shift, the largest amplitude difference occurs in the zeroth transmitted s channel. Both refinement axes matter. The order-only and grid-only changes are 0.0293 and 0.0201, respectively. The matched-operator test accounts for most of the quick gap, and the native gap stays at 0.0658 at the finer settings for this coupled bilayer.

### C06

The 4:1 supercell redistributes power among many propagating orders. At 1420 nm, p efficiency into the target transmitted order $(+1,0)$ is 0.248 (Meent), 0.584 (grcwa and torcwa), and 0.346 (published Lumerical). The open-source order-only change of 0.656 is about thirteen times the grid-only change. Matching the actual Fourier basis reduces the Lumerical–grcwa amplitude gap from 0.824 to 0.194. The finer native Meent–grcwa gap is still 0.586. In the direct-DFS control the two open-source engines agree to round-off for these asymmetrically positioned pillars. These tests leave the convergence of the native solvers and the effect of prescribing different orders along the two axes open.

## Conclusion

The matched-operator tests establish that the finite-order material representation accounts for most of the native Meent discrepancy at the selected periodic points. The higher actual Fourier basis in the published Lumerical profile accounts for much of the selected discrepancy in seven cases against grcwa. The largest effects are resonance shifts in C02 and diffraction-order redistribution in C06. Vertical slicing affects B04, grid sampling is especially important for C04, and the B06 Lumerical phase discrepancy tracks half a mesh interval. Agreement with a shared operator verifies consistency for that discretized problem. The finer native Meent–grcwa results still exceed the benchmark amplitude tolerance in eleven cases at the selected points.

## Reproduce

From the repository root in the project environment, run the following command. The diagnostic results are written into the `periodic_diagnostics` section of [the benchmark data](results/benchmark.json), and the C02 plot is saved under `results/figures/C02/`.

```powershell
& .\.venv\Scripts\python.exe scripts\diagnose_periodic.py
```

Use `--open-only` to rerun the open-source controls independently. Run the diagnostic again after republishing the benchmark to capture the new quick-sweep points.
