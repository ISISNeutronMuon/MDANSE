import numpy as np
import pytest
from MDANSE.MolecularDynamics.UnitCell import UnitCell


@pytest.fixture
def cubic():
    return UnitCell(np.diag([5., 5., 5.]))

@pytest.fixture
def orthorhombic():
    return UnitCell(np.diag([4., 5., 6.]))

@pytest.fixture
def hexagonal():
    return UnitCell([[0., 2.71535, 2.71535],
                     [2.71535, 0., 2.71535],
                     [2.71535, 2.71535, 0.]])

@pytest.fixture
def cell(request, cubic, orthorhombic, hexagonal):
    if request.param == "cubic":
        return cubic
    if request.param == "orthorhombic":
        return orthorhombic
    if request.param == "hexagonal":
        return hexagonal
    if request.param is None:
        return None

    raise KeyError(f"Unknown cell {request.param!r}")
