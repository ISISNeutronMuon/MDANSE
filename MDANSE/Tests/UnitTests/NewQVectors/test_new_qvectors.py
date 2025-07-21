import pytest

from MDANSE.Framework.NewQVectors import QVectorGenerator


@pytest.mark.parametrize("instance", [
    "ListQVectors",
    "GeneratorQVectors",
    "GridQVectors",
    "LinearQVectors",
    "PathLinearQVectors",
    "SphericalQVectors",
    "LatticeSphericalQVectors",
    "CircularQVectors",
    "PathSegmentQVectors",
    "LatticeLinearQVectors",
])
def test_factory(instance):
    subclass_dict = QVectorGenerator.indirect_subclass_dictionary()
    assert subclass_dict[instance].__name__ == instance
