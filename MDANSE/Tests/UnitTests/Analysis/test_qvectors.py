import copy

import numpy as np
import pytest
from test_helpers.paths import CONV_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.QVectors.CircularQVectors import circle_rotation_matrix
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.MolecularDynamics.UnitCell import UnitCell

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"


VEC_PARAMS = {
        "seed": 1,
        "shells": (6.0, 11.01, 5.0),
        "n_vectors": 10,
        "width": 1.0,
        "q_start": (0,0,0),
        "q_end": (5,2,2),
        "q_step": 0.02,
        "axis": (1,1,0),
        "hrange": (0,6,1),
        "krange": (0,6,1),
        "lrange": (0,6,1),
        "h": (0,6,1),
        "k": (0,6,1),
        "l": (0,6,1),
        "start": (0,0,0),
        "step": (1,0,0),
        "direction": (1,1,1),
    }

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

def test_classmethod_lattice_vectors_with_weights():
    cell1 = UnitCell([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    vectors = np.array([[0,0,0,0],
                        [0,1,2,0],
                        [0,0,0,0]])*2*np.pi
    vecs, weights = IQVectors.lattice_vectors_with_weights(vectors, cell1)
    assert vecs.shape == (3,3)
    assert vecs.shape[1] == len(weights)


def test_circle_rotation_matrix_right_angle():
    rotmat = circle_rotation_matrix([1,0,0])
    assert np.isclose(np.trace(rotmat), np.sum(rotmat))


def test_circular_vectors_can_rotate():
    cell1 = UnitCell([[0, 45, 45], [45, 0, 45], [45, 45, 0]])
    qvg = IQVectors.create("CircularQVectors", cell1)
    qvg.setup(VEC_PARAMS)
    qvg.generate()
    assert len(qvg["q_vectors"]) == 2

def test_dispersion_and_dispersion_lattice_agree():
    vec_par = copy.deepcopy(VEC_PARAMS)
    vec_par["q_step"] = 2.0*np.pi
    vec_par["q_end"] = [20.01*np.pi,0,0]
    cell1 = UnitCell([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    disp = IQVectors.create("DispersionQVectors", cell1)
    disp.setup(vec_par)
    disp.generate()
    disp_latt = IQVectors.create("DispersionLatticeQVectors", cell1)
    disp_latt.setup(vec_par)
    disp_latt.generate()
    common_keys = set(disp["q_vectors"].keys()).intersection(set(disp_latt["q_vectors"].keys()))
    for key in sorted(common_keys):
        print(key, disp["q_vectors"][key]["q_vectors"], disp_latt["q_vectors"][key]["q_vectors"])
        assert np.allclose(disp["q_vectors"][key]["q_vectors"], disp_latt["q_vectors"][key]["q_vectors"])


@pytest.mark.parametrize("qvector_generator", [
 'LinearQVectors',
 'DispersionQVectors',])
def test_directional_qvectors_for_nonorthogonal_cells(qvector_generator):
    """These generators take input in reciprocal vector units (q),
    and so changing the order of the lattice vectors will change
    the order of the columns in the HKL arrays."""
    cell1 = UnitCell([[0, 45, 45], [45, 0, 45], [45, 45, 0]])
    cell2 = UnitCell([[45, 45, 0], [45, 0, 45], [0, 45, 45]])
    qvecs = []
    for cell in (cell1, cell2):
        qvg = IQVectors.create(qvector_generator, cell)
        qvg.setup(VEC_PARAMS)
        qvg.generate()
        qvecs.append(qvg)
    qvec_generator1, qvec_generator2 = qvecs[0], qvecs[1]

    np.testing.assert_allclose(
            sorted(qvec_generator1["q_vectors"]),
            sorted(qvec_generator2["q_vectors"]),
            atol=1e-7,
            rtol=1e-7,
        )

    key_array = np.array([float(x) for x in qvec_generator2["q_vectors"].keys()])

    for key1 in qvec_generator1["q_vectors"]:
        key2 = key_array[np.where(np.isclose(key1, key_array))][0]
        for col1, col2 in [(0,2), (1,1), (2,0)]:
            np.testing.assert_allclose(
                qvec_generator1["q_vectors"][key1]["hkls"][col1, :],
                qvec_generator2["q_vectors"][key2]["hkls"][col2, :],
                atol=1e-7,
                rtol=1e-7,
            )


@pytest.mark.parametrize("qvector_generator", [
 'DispersionLatticeQVectors',])
def test_directional_hkl_vectors_for_nonorthogonal_cells(qvector_generator):
    """This generator takes input in the HKL units, so there is no need
    to change the sequence of the columns in the output HKL arrays."""
    cell1 = UnitCell([[0, 45, 45], [45, 0, 45], [45, 45, 0]])
    cell2 = UnitCell([[45, 45, 0], [45, 0, 45], [0, 45, 45]])
    qvecs = []
    for cell in (cell1, cell2):
        qvg = IQVectors.create(qvector_generator, cell)
        qvg.setup(VEC_PARAMS)
        qvg.generate()
        qvecs.append(qvg)
    qvec_generator1, qvec_generator2 = qvecs[0], qvecs[1]

    np.testing.assert_allclose(
            sorted(qvec_generator1["q_vectors"]),
            sorted(qvec_generator2["q_vectors"]),
            atol=1e-7,
            rtol=1e-7,
        )

    key_array = np.array([float(x) for x in qvec_generator2["q_vectors"].keys()])

    for key1 in qvec_generator1["q_vectors"]:
        key2 = key_array[np.where(np.isclose(key1, key_array))][0]
        for col1 in range(3):
            np.testing.assert_allclose(
                qvec_generator1["q_vectors"][key1]["hkls"][col1, :],
                qvec_generator2["q_vectors"][key2]["hkls"][col1, :],
                atol=1e-7,
                rtol=1e-7,
            )

@pytest.mark.parametrize("qvector_generator", IQVectors.indirect_subclasses())
def test_qvector_to_hkl_conversion(trajectory, qvector_generator):
    instance = IQVectors.create(qvector_generator, trajectory.unit_cell(0))
    instance.setup({"shells": (5.0, 50.0, 10.0)})
    unit_cell = trajectory.unit_cell(0)
    instance.generate()
    try:
        instance._configuration["shells"]
    except KeyError:
        print(f"{qvector_generator} has no shells")
        return
    for q in instance._configuration["shells"]["value"][:2]:
        if instance._configuration["q_vectors"][q] is None:
            continue
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

    instance = IQVectors.create(qvector_generator, trajectory.unit_cell(0))
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

@pytest.mark.parametrize("qvector_generator", [
 'SphericalLatticeQVectors',
 'CircularLatticeQVectors',
 'LinearLatticeQVectors'])
def test_weights_flag_resets_weights(qvector_generator: str, weights_flag: bool = True):
    """Check if the weights override flag resets vector weights to 1."""
    vec_par = copy.deepcopy(VEC_PARAMS)
    cell = UnitCell([[45, 45, 0], [45, 0, 45], [0, 45, 45]])
    qvg = IQVectors.create(qvector_generator, cell)
    vec_par["force_equal_weights"] = weights_flag
    vec_par["n_vectors"] = 1000
    vec_par["shells"] =  (6.0, 7.0, 2.0)
    qvg.setup(vec_par)
    qvg.generate()
    for key1 in qvg["q_vectors"]:
        weights = qvg["q_vectors"][key1]["weights"]
        np.testing.assert_allclose(weights, 1)
        assert np.isclose(0, np.std(weights))

