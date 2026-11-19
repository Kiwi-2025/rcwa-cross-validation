from typing import Protocol

from ..models import CaseSpec, SimulationResult, SolverSettings


class Unavailable(RuntimeError):
    """The required solver runtime is absent."""


class Adapter(Protocol):
    def probe(self) -> dict: ...
    def solve(self, case: CaseSpec, settings: SolverSettings) -> SimulationResult: ...
