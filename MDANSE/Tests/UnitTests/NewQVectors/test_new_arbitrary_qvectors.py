from collections.abc import Generator
from contextlib import nullcontext as success
from typing import Optional

import numpy as np
import pytest
from MDANSE.Framework.NewQVectors import (GeneratorQVectors, ListQVectors,
                                          QVectorData)
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from numpy.typing import NDArray
from test_helpers.common_fixtures import cell, cubic, hexagonal, orthorhombic


@pytest.mark.parametrize("cell, params, expected", [
    (None, {"qvectors": [[1, 1, 1], [2, 2, 2]]}, success([[1., 1., 1.],
                                                          [2., 2., 2.]])),

    ("cubic", {"qvectors": [[1, 1, 1], [2, 2, 2]]}, success([[1., 1., 1.],
                                                             [2., 2., 2.]])),

    ("orthorhombic", {"qvectors": [[1, 1, 1], [2, 2, 2]]}, success([[1., 1., 1.],
                                                                    [2., 2., 2.]])),

    ("hexagonal", {"qvectors": [[1, 1, 1], [2, 2, 2]]}, success([[1., 1., 1.],
                                                                 [2., 2., 2.]])),

    (None, {"qvectors": [[1, 1, 1], [2, 2, 2]], "hkl": True}, pytest.raises(ValueError, match="requires defined `lattice`")),

    ("cubic", {"qvectors": [[1, 1, 1], [2, 2, 2]], "hkl": True}, success([[0.2, 0.2, 0.2],
                                                                          [0.4, 0.4, 0.4]])),

    ("orthorhombic", {"qvectors": [[1, 1, 1], [2, 2, 2]], "hkl": True}, success([[0.25, 0.2, 1/6],
                                                                                 [0.5, 0.4, 1/3]])),

    ("hexagonal", {"qvectors": [[1, 1, 1], [2, 2, 2]], "hkl": True}, success([[0.18413832, 0.18413832, 0.18413832],
                                                                              [0.36827664, 0.36827664, 0.36827664]])),

], indirect=["cell"])
def test_list_qvectors(cell, params, expected):
    with expected as val:
        qvec = ListQVectors(lattice=cell, **params)
        results = [QVectorData(q, cell) for q in val]
        assert list(qvec) == results


def naive_generator(lattice: Optional[UnitCell]) -> Generator[NDArray[float], None, None]:
    my_favourite_constants = [np.pi, np.e, np.euler_gamma]

    for const in my_favourite_constants:
        yield np.array([const, const, const])


@pytest.mark.parametrize("cell, args, kwargs, expected", [
    (None, (naive_generator,), {"returns_qvec_data": False}, success([[np.pi]*3, [np.e]*3, [np.euler_gamma]*3])),
], indirect=["cell"])
def test_generator_qvectors(cell, args, kwargs, expected):
    with expected as val:
        qvec = GeneratorQVectors(*args, lattice=cell, **kwargs)
        results = [QVectorData(q, cell) for q in val]
        assert list(qvec) == results
