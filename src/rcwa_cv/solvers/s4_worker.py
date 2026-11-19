"""S4 solves in Linux. Exchange one resolved geometry and numeric result over JSON."""
from dataclasses import asdict
import json
import sys

import numpy as np

from ..models import CaseSpec, Layer, Shape, SolverSettings
from ..geometry import rectangular_orders
from ..conventions import incident_basis, result_from_xy, wavevectors


S4_REVISION = "9569f5e555b967a4324eb1ea593d0f9f40761a61"


def _complex(value):
    if isinstance(value, complex):
        return [value.real, value.imag]
    raise TypeError(type(value).__name__)


def encode(case, settings):
    return json.dumps({"case": asdict(case), "settings": asdict(settings)}, default=_complex)


def decode(data):
    props = data["case"]
    layers = []
    for layer in props.pop("layers"):
        shapes = tuple(Shape(**dict(s, epsilon=complex(*s["epsilon"]))) for s in layer["shapes"])
        layers.append(Layer(layer["thickness"], complex(*layer["epsilon"]), shapes))
    return CaseSpec(**props, layers=tuple(layers)), SolverSettings(**data["settings"])


def solve(case, settings):
    import S4

    lx, ly = case.period
    lattice = ((lx, 0), (0, ly)) if case.dimensions == 2 else lx
    solver = S4.New(Lattice=lattice, NumBasis=len(rectangular_orders(case, settings)))
    if case.dimensions == 2:
        solver.SetOptions(LatticeTruncation="Parallelogramic")
    materials = {}

    def name(eps):
        if eps not in materials:
            materials[eps] = f"m{len(materials)}"
            solver.SetMaterial(Name=materials[eps], Epsilon=complex(eps))
        return materials[eps]

    solver.AddLayer(Name="incident", Thickness=0, Material=name(case.incident))
    for i, layer in enumerate(case.layers):
        key = f"layer{i}"
        solver.AddLayer(Name=key, Thickness=layer.thickness, Material=name(layer.epsilon))
        for shape in layer.shapes:
            material = name(shape.epsilon)
            if case.dimensions == 1:
                solver.SetRegionRectangle(Layer=key, Material=material,
                                          Center=(shape.center[0], 0), Angle=0,
                                          Halfwidths=(shape.width/2, 0))
            elif shape.kind == "circle":
                solver.SetRegionCircle(Layer=key, Material=material, Center=tuple(shape.center),
                                       Radius=shape.width/2)
            else:
                solver.SetRegionRectangle(Layer=key, Material=material, Center=tuple(shape.center),
                                          Angle=shape.rotation, Halfwidths=(shape.width/2, shape.length/2))
    solver.AddLayer(Name="exit", Thickness=0, Material=name(case.exit))
    solver.SetFrequency(1/case.wavelength)
    orders = np.asarray(solver.GetBasisSet(), dtype=int)
    zero = np.flatnonzero(np.all(orders == 0, axis=1))[0]
    transverse, kz2 = wavevectors(case, orders)
    source, kzi = incident_basis(case)
    fields = np.zeros((2, len(orders), 2, 2), complex)

    def electric(modes, port, mask, sign):
        eps = (case.incident, case.exit)[port]
        kz = sign * np.sqrt(kz2[port, mask])
        k = np.column_stack((transverse[mask], kz))
        hx, hy = np.asarray(modes).reshape(2, -1)[:, mask]
        hz = -(k[:, 0]*hx + k[:, 1]*hy)/kz
        return -np.cross(k, np.column_stack((hx, hy, hz)))/eps

    for p in range(2):
        solver.SetExcitationPlanewave(IncidenceAngles=(case.theta, case.phi),
                                      sAmplitude=complex(p == 0), pAmplitude=complex(p == 1))
        forward, reflect = solver.GetAmplitudes(Layer="incident")
        transmit, _ = solver.GetAmplitudes(Layer="exit")
        only_zero = np.arange(len(orders)) == zero
        actual_source = electric(forward, 0, only_zero, 1)[0]
        scale = np.dot(source[:, p], actual_source)
        if abs(scale) < .1 or np.linalg.norm(actual_source-scale*source[:, p]) > 1e-8:
            raise ValueError("S4 incident polarization does not match the requested Cartesian basis.")
        for port, modes in enumerate((reflect, transmit)):
            mask = kz2[port] > 1e-10
            fields[port, mask, :, p] = electric(modes, port, mask, -1 if port == 0 else 1)[:, :2]/scale
    return result_from_xy(case, orders, fields, {"version": S4_REVISION, "device": "CPU"})


def main():
    answer = solve(*decode(json.load(sys.stdin)))
    print(json.dumps({**answer.metadata, "orders": answer.orders.tolist(),
                      "real": answer.amplitude.real.tolist(), "imag": answer.amplitude.imag.tolist()}))


if __name__ == "__main__":
    main()
