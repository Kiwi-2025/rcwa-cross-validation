from dataclasses import replace
import json

import numpy as np
import pytest

from rcwa_cv.case_loader import catalog, load_case, resolve
from rcwa_cv.geometry import midpoint_phase, rectangular_orders, shape_fourier_grid
from rcwa_cv.models import SolverSettings
from rcwa_cv.references import multilayer
from rcwa_cv.reporting.benchmark import compare_certified, optical_data, read_sample
from rcwa_cv.reporting.tables import compare_to_lumerical, summarize
from rcwa_cv.solvers import MODULES, adapter
from rcwa_cv.solvers.lumerical import build_script
from rcwa_cv.validation.compare import differences, meets
from rcwa_cv.validation.physics import checks


SETTINGS = SolverSettings(order=0, grid=16, slices=1)


def test_catalog_and_lumerical_exports():
    assert len(catalog("A")) == 4
    assert len(catalog("B")) == len(catalog("C")) == 6
    for path in catalog():
        case = resolve(load_case(path), "nominal", {}, SETTINGS)
        assert path.parent.name == case.id
        script = build_script(case, SETTINGS)
        assert 'run("RCWA");' in script
        assert 'getresult("RCWA","grating_characterization")' in script


def test_case_notebooks_and_models_are_present():
    for path in catalog():
        case_id = path.parent.name
        notebook = json.loads((path.parent/f"{case_id}.ipynb").read_text(encoding="utf-8"))
        description = "".join(notebook["cells"][0]["source"])
        assert description.index("## Mathematical and physical model") < description.index("## Physical scenario")
        assert "## Possible applications" in description
        assert not (path.parent/"README.md").exists()
        code = "\n".join("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"]=="code")
        compile(code, f"{case_id}.ipynb", "exec")
        for name, module in MODULES.items():
            assert f"from rcwa_cv.solvers.{module} import" in code
            assert f'results["{name}"]' in code
        assert (path.parent/"model.fsp").stat().st_size > 0
        assert 'run("RCWA");' in (path.parent/"model.lsf").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["meent", "grcwa"])
@pytest.mark.parametrize("id,theta", [("A01",30),("A02",0),("A03",0),("A04",0)])
def test_planar_agreement(name, id, theta):
    case = resolve(load_case(catalog(id)[0]), "nominal", {"theta_deg":theta}, SETTINGS)
    exact = multilayer.solve(case, SETTINGS)
    other = adapter(name).solve(case, SETTINGS)
    assert meets(differences(exact, other), 1e-8)
    assert max(checks(other, case.lossy).values()) < 1e-8


def test_fresnel_total_internal_reflection():
    spec = load_case(catalog("A01")[0])
    point = resolve(spec, "reverse", {**spec["variants"]["reverse"], "theta_deg":55}, SETTINGS)
    result = multilayer.solve(point, SETTINGS)
    assert result.propagating.tolist() == [[True], [False]]
    assert np.allclose(result.totals, [[1, 1],[0, 0]])
    assert np.all(np.abs(result.amplitude[0,0].diagonal().imag) > .1)


def test_torcwa_uses_real_cuda():
    pytest.importorskip("torch")
    pytest.importorskip("torcwa")
    import torch
    if not torch.cuda.is_available():
        pytest.skip("CUDA device not available")
    case = resolve(load_case(catalog("A02")[0]), "nominal", {}, SETTINGS)
    result = adapter("torcwa").solve(case, SETTINGS)
    assert result.metadata["device"].startswith("cuda:")
    assert result.metadata["precision"] == "complex128"
    assert result.metadata["peak_allocated_bytes"] > 0
    assert meets(differences(multilayer.solve(case, SETTINGS), result), 1e-8)


def test_grating_translation_changes_only_diffraction_phase():
    settings = SolverSettings(order=5, grid=128, slices=1)
    case = resolve(load_case(catalog("B01")[0]), "nominal", {}, settings)
    layer, = case.layers
    shape, = layer.shapes
    translated = replace(shape, center=(case.period[0]/4, 0))
    shifted = replace(case, layers=(replace(layer, shapes=(translated,)),))
    solve = adapter("grcwa").solve
    first, second = solve(case, settings), solve(shifted, settings)
    factor = np.exp(-.5j*np.pi*first.orders[:,0])[None, :, None, None]
    assert np.max(abs(first.amplitude[1, first.orders[:,0]==1])) > .1
    assert np.allclose(second.power, first.power, atol=1e-10)
    assert np.allclose(second.amplitude, first.amplitude*factor, atol=1e-10)


def test_matched_meent_operator_for_translated_two_dimensional_grating():
    settings = SolverSettings(order=3, grid=96, slices=1)
    case = resolve(load_case(catalog("C06")[0]), "nominal", {"wavelength_nm":633}, settings)
    layer, = case.layers
    pillar, = layer.shapes
    case = replace(case, layers=(replace(layer, shapes=(replace(pillar, center=(71, 36)),)),))
    reference = adapter("grcwa").solve(case, settings)
    result = adapter("meent").solve(case, settings, material_operator="direct-dfs")
    assert reference.propagating[1].sum() == 5
    assert meets(differences(reference, result), 1e-8)


def test_closed_form_shape_coefficients_are_independent_of_fft_grid():
    settings = SolverSettings(5, 21, 1)
    case = resolve(load_case(catalog("C03")[0]), "nominal", {"radius_nm": 50}, settings)
    layer = case.layers[0]
    orders = np.asarray([(m, n) for m in range(-10, 11) for n in range(-10, 11)])
    coefficients = []
    for grid in (21, 33):
        values = shape_fourier_grid(layer, case, grid, settings.order)
        fft = np.fft.fft2(values) / grid**2
        coefficients.append(fft[orders[:, 0], orders[:, 1]] * midpoint_phase(orders, grid))
    assert np.allclose(*coefficients, atol=1e-12)
    assert coefficients[0][220] == pytest.approx(1 + (1.69 - 1) * np.pi * 50**2 / 300**2)
    assert np.allclose(coefficients[0], coefficients[0].reshape(21, 21).T.ravel())


def test_asymmetric_basis_matches_published_coordinates():
    settings = SolverSettings(4, 33, 1, 2)
    case = resolve(load_case(catalog("C06")[0]), "nominal", {"wavelength_nm": 633}, settings)
    orders = rectangular_orders(case, settings)
    solver = adapter("grcwa").solve(case, settings, exact_shapes=True)
    assert np.array_equal(solver.orders, orders)
    assert max(checks(solver, case.lossy).values()) < 1e-8
    script = build_script(case, settings, match_fourier_order=True)
    assert 'set("max number ku",4);' in script and 'set("max number kv",2);' in script


@pytest.mark.parametrize("name", ["grcwa", "torcwa"])
@pytest.mark.parametrize("case_id", ["B02", "B05"])
def test_li_adapter_preserves_te_and_resolves_the_tm_material_product(name, case_id):
    if name == "torcwa":
        torch = pytest.importorskip("torch")
        pytest.importorskip("torcwa")
        if not torch.cuda.is_available():
            pytest.skip("CUDA device not available")
    settings = SolverSettings(24, 2048, 1)
    case = resolve(load_case(catalog(case_id)[0]), "nominal", {"wavelength_nm": 1200}, settings)
    solve = adapter(name).solve
    native = solve(case, settings)
    modified = solve(case, settings, li_factorization=True)
    reference = adapter("meent").solve(case, settings)
    assert modified.metadata["numerical_mode"] == "1D Li inverse rule"
    assert np.allclose(native.totals[:, 0], modified.totals[:, 0], atol=1e-9, rtol=0)
    assert np.max(abs(native.totals[:, 1] - modified.totals[:, 1])) > 1e-3
    assert meets(differences(reference, modified), 2e-5, .02)


def test_reporting_uses_lumerical_and_requires_a_common_point():
    spec = load_case(catalog("A01")[0])
    case = resolve(spec, "reverse", {"theta_deg": 55}, SETTINGS)
    original = multilayer.solve(case, SETTINGS)
    restored = read_sample(optical_data(original))
    assert meets(differences(original, restored), 0)
    completed = {"status": "COMPLETE", "completed": [
        {"index": 0, "converged": True, "physics": checks(original, case.lossy)}]}
    manifest = {"case": "A01", "points": [{}], "representative": False, "point_limit": None,
                "solvers": {name: completed for name in (*MODULES, "reference")}}
    results = {name: {0: original} for name in (*MODULES, "reference")}
    results["lumerical"] = {0: restored}
    pairs = compare_to_lumerical(manifest, results)
    assert [pair["solvers"] for pair in pairs] == [
        ["meent", "lumerical"], ["torcwa", "lumerical"], ["grcwa", "lumerical"]]
    assert summarize(manifest, pairs)["status"] == "PASS"
    results["lumerical"] = {}
    pairs = compare_to_lumerical(manifest, results)
    assert all(pair["status"] == "NOT_RUN" for pair in pairs)
    assert summarize(manifest, pairs)["status"] == "NOT_RUN"


def test_benchmark_reports_only_observables_with_paired_convergence():
    spec = load_case(catalog("A02")[0])
    original = multilayer.solve(resolve(spec, "nominal", {}, SETTINGS), SETTINGS)
    phased = replace(original, amplitude=original.amplitude * np.exp(0.1j))
    full = {"power_converged": True, "full_converged": True, "sample": optical_data(original)}
    power_only = dict(full, full_converged=False, sample=optical_data(phased))
    field_mismatch = dict(full, sample=optical_data(phased))
    unverified = {"power_converged": False, "full_converged": False}
    record = {"case": "C02", "solvers": {"meent": [unverified, full], "torcwa": [power_only, full],
                                        "grcwa": [field_mismatch, full], "lumerical": [full, unverified]}}
    pairs = compare_certified(record)
    assert pairs["meent"] == []
    assert pairs["torcwa"] == [{"point": 0, "power": 0, "power_pass": True}]
    assert len(pairs["grcwa"]) == 1
    assert pairs["grcwa"][0]["power_pass"]
    assert not pairs["grcwa"][0]["full_pass"]


def test_class_c_requires_all_four_at_the_same_observable_level():
    spec = load_case(catalog("A02")[0])
    result = multilayer.solve(resolve(spec, "nominal", {}, SETTINGS), SETTINGS)
    full = {"power_converged": True, "full_converged": True, "sample": optical_data(result)}
    power = dict(full, full_converged=False)
    pending = dict(power, power_converged=False)
    record = {"case": "C02", "joint_convergence": True, "solvers": {
        "meent": [pending, power, full], "torcwa": [full, full, full],
        "grcwa": [full, full, full], "lumerical": [full, full, full],
    }}
    for pairs in compare_certified(record).values():
        assert [row["point"] for row in pairs] == [1, 2]
        assert "full_pass" not in pairs[0]
        assert pairs[1]["full_pass"]
    replays = {name: {1: result, 2: result} for name in MODULES}
    del replays["meent"][2]
    assert all([row["point"] for row in pairs] == [1]
               for pairs in compare_certified(record, replays).values())


@pytest.mark.parametrize("case_id", ["C01", "C02", "C05", "C06"])
def test_torcwa_compact_exterior_coupling_matches_native_gpu(case_id):
    torch = pytest.importorskip("torch")
    pytest.importorskip("torcwa")
    if not torch.cuda.is_available():
        pytest.skip("CUDA device not available")
    settings = SolverSettings(3, 96, 1, 2)
    case = resolve(load_case(catalog(case_id)[0]), "nominal", {}, settings)
    solve = adapter("torcwa").solve
    native, compact = solve(case, settings, compact=False), solve(case, settings, compact=True)
    assert meets(differences(native, compact), 1e-10, 1e-7)
    assert compact.metadata["device"].startswith("cuda:")
