import pytest
import tempfile
import os
from os import path
import h5py
from MDANSE.Src.Framework.Formats.NetCDF_HDF_convert import HDF5TrajectoryConverter

@pytest.fixture
def example_trajectory_file_from_registry():
    example_traj = REGISTRY['example_trajectory']()
    return example_traj

@pytest.mark.parametrize('interp_order', [1, 2, 3])
def test_trajectory_conversion(create_sample_nc_file, tmpdir, interp_order):
    nc_filename = create_sample_nc_file
    h5_filename = str(tmpdir.join("output_trajectory.h5"))
    converter = HDF5TrajectoryConverter(nc_filename)
    converter.convert_trajectory_to_hdf5(h5_filename)
    assert path.exists(h5_filename)
    assert path.isfile(h5_filename)
    
    # testing logic
    parameters = {}
    parameters['trajectory'] = short_traj
    temp_name = tempfile.mktemp()
    parameters['frames'] = (0, 10, 1)
    parameters['interpolation_order'] = interp_order
    parameters['output_files'] = (temp_name, ('hdf',))

    temp = REGISTRY['job']['temp']()
    temp.run(parameters, status=True)

    assert path.exists(temp_name + '.h5')
    assert path.isfile(temp_name + '.h5')
    os.remove(temp_name + '.h5')