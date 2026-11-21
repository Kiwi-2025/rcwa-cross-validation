from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Shape:
    kind: str
    epsilon: complex
    center: tuple[float, float] = (0, 0)
    width: float = 0
    length: float = 0
    rotation: float = 0


@dataclass(frozen=True)
class Layer:
    thickness: float
    epsilon: complex
    shapes: tuple[Shape, ...] = ()


@dataclass(frozen=True)
class CaseSpec:
    id: str
    variant: str
    dimensions: int
    period: tuple[float, float]
    incident: float
    exit: float
    wavelength: float
    theta: float
    phi: float
    layers: tuple[Layer, ...]

    @property
    def thickness(self):
        return sum(layer.thickness for layer in self.layers)

    @property
    def lossy(self):
        return any(layer.epsilon.imag > 0 or any(s.epsilon.imag > 0 for s in layer.shapes)
                   for layer in self.layers)


@dataclass(frozen=True)
class SolverSettings:
    order: int
    grid: int
    slices: int
    order_y: int | None = None


@dataclass
class SimulationResult:
    orders: np.ndarray             # shape (N, 2)
    propagating: np.ndarray        # shape (2, N), port order R, T
    power: np.ndarray              # shape (2, N, 2), input order s, p
    amplitude: np.ndarray          # shape (2, N, 2, 2), output then input
    totals: np.ndarray             # shape (2, 2), port then input
    metadata: dict
