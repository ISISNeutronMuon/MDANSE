import pytest
from MDANSE.MolecularDynamics.Trajectory import \
    Trajectory
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import \
    IInstrumentResolution
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"


@pytest.fixture(scope="module")
def trajectory():
    trajectory = Trajectory(short_traj)
    yield trajectory

@pytest.mark.parametrize("resolution_generator", IInstrumentResolution.subclasses())
def test_disf(tmp_path, trajectory, resolution_generator):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "q_vectors": (
            "SphericalLatticeQVectors",
            {"seed": 0, "shells": (5.0, 36, 10.0), "n_vectors": 10, "width": 9.0},
        ),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_incoherent",
    }

    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    instance = IInstrumentResolution.create(resolution_generator)
    resolution_defaults = {
        name: value[1]["default"] for name, value in instance.settings.items()
    }

    print(resolution_generator)
    print(resolution_defaults)

    parameters["instrument_resolution"] = (
        resolution_generator,
        resolution_defaults,
    )

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()


@pytest.mark.parametrize("resolution_generator", IInstrumentResolution.subclasses())
def test_dos(generate_benchmarks, tmp_path, trajectory, resolution_generator):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    text_file = tmp_path / "output_text.tar"
    result_file = RESULTS_DIR / f"dos_{resolution_generator}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_incoherent",
    }

    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")

    instance = IInstrumentResolution.create(resolution_generator)
    resolution_defaults = {
        name: value[1]["default"] for name, value in instance.settings.items()
    }

    print(resolution_generator)
    print(resolution_defaults)

    parameters["instrument_resolution"] = (
        resolution_generator,
        resolution_defaults,
    )

    disf = IJob.create("DensityOfStates")
    disf.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    keys = [f"{fn}/{elem}"
            for fn in ("dos", "vacf")
            for elem in ("Cu", "S", "Sb", "total")]

    compare_hdf5(out_file,
                 result_file,
                 keys,
                 scale_result=True,
                 scale_benchmark=True,
                 compare_axis=True)


def test_dos_is_reproducible(tmp_path, trajectory):
    resolution_generator = "ideal"

    temp_name1 = tmp_path / "output1"
    temp_name2 = tmp_path / "output2"
    temp_name3 = tmp_path / "output3"

    for temp_name in [temp_name1, temp_name2, temp_name3]:
        parameters = {
            "atom_selection": None,
            "atom_transmutation": None,
            "frames": (0, 10, 1, 5),
            "instrument_resolution": ("Ideal", {}),
            "running_mode": ("single-core",),
            "trajectory": short_traj,
            "weights": "b_incoherent",
        }

        parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")

        instance = IInstrumentResolution.create(resolution_generator)
        resolution_defaults = {
            name: value[1]["default"] for name, value in instance.settings.items()
        }

        print(resolution_generator)
        print(resolution_defaults)

        parameters["instrument_resolution"] = (
            resolution_generator,
            resolution_defaults,
        )

        disf = IJob.create("DensityOfStates")
        disf.run(parameters, status=True)

    keys = [f"{fn}/{elem}"
            for fn in ("dos", "vacf")
            for elem in ("Cu", "S", "Sb", "total")]

    compare_hdf5(temp_name1.with_suffix(".mda"),
                 temp_name2.with_suffix(".mda"),
                 keys,
                 scale_result=True,
                 scale_benchmark=True,
                 compare_axis=True)
    compare_hdf5(temp_name1.with_suffix(".mda"),
                 temp_name3.with_suffix(".mda"),
                 keys,
                 scale_result=True,
                 scale_benchmark=True,
                 compare_axis=True)
