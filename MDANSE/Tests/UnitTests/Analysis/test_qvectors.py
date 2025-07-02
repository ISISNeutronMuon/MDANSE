import numpy as np
import pytest
from test_helpers.paths import CONV_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.MolecularDynamics.UnitCell import UnitCell

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"


@pytest.fixture(scope="module")
def trajectory():
    trajectory = Trajectory(short_traj)
    yield trajectory


def test_qvectors_for_nonorthogonal_cell():
    cell = UnitCell([[15, 0, 0], [0, 16, 0], [8, 0, 23]])
    start_vectors = np.array([[1, 0, 0, 1, 2], [0, 1, 0, 1, 2], [0, 0, 1, 1, 2]])
    temporary_hkls = IQVectors.qvectors_to_hkl(start_vectors, cell)
    final_vectors = IQVectors.hkl_to_qvectors(temporary_hkls, cell)
    np.testing.assert_allclose(
        start_vectors,
        final_vectors,
        atol=1e-7,
        rtol=1e-7,
    )


@pytest.mark.parametrize("qvector_generator", IQVectors.indirect_subclasses())
def test_qvector_to_hkl_conversion(trajectory, qvector_generator):
    instance = IQVectors.create(qvector_generator, trajectory.configuration(0))
    instance.setup({"shells": (5.0, 50.0, 10.0)})
    unit_cell = trajectory.unit_cell(0)
    instance.generate()
    try:
        instance._configuration["shells"]
    except KeyError:
        print(f"{qvector_generator} has no shells")
        return
    for q in instance._configuration["shells"]["value"][:2]:
        try:
            original_qvectors = instance._configuration["q_vectors"][q]["q_vectors"]
        except KeyError:
            return
        if len(original_qvectors) == 0:
            return
        hkls = instance.qvectors_to_hkl(original_qvectors, unit_cell)
        recalculated_qvectors = instance.hkl_to_qvectors(hkls, unit_cell)
        assert np.allclose(original_qvectors, recalculated_qvectors)


@pytest.mark.parametrize("qvector_generator", IQVectors.indirect_subclasses())
def test_disf(tmp_path, trajectory, qvector_generator):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_incoherent",
    }

    instance = IQVectors.create(qvector_generator, trajectory.configuration())
    qvector_defaults = {
        name: value[1]["default"] for name, value in instance.settings.items()
    }

    if len(qvector_defaults) < 1:
        return

    parameters["q_vectors"] = (qvector_generator, qvector_defaults)

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
