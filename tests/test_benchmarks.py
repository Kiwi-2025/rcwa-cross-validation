from dataclasses import replace

import numpy as np
import pytest

from rcwa_cv.case_loader import catalog, load_case, resolve
from rcwa_cv.models import SolverSettings
from rcwa_cv.references import multilayer
from rcwa_cv.solvers import adapter
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
