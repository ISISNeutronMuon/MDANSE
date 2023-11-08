# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Formats/NetCDFFormat.py
# @brief     Implements module/class/test NetCDFFormat
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
"""
Converts NetCDF files to HDF5 format in the MDANSE project.
This script provides functions to convert NetCDF files to HDF5 format. 
It includes functions for reading the NetCDF file header,
 removing null characters, and performing the conversion. 
Proper exception handling and file management are implemented.
For more information about the MDANSE project, visit: https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx

"""
import os
import netCDF4 as nc
import h5py
import sys
import numpy as np
 
def convert_netcdf_to_hdf5_mdanse(input_file, output_file):
    try:
        chemical_system_vars = {'atom_clusters', 'atoms', 'contents'}
        configuration_vars = {'coordinates', 'time'}
        unit_cell_vars = {'unit_cell'}
 
        rootgrp = nc.Dataset(input_file, "r")
        with h5py.File(output_file, "w") as f:
            chemical_system_grp = f.create_group('chemical_system')
            configuration_grp = f.create_group('configuration')
            unit_cell_grp = f.create_group('unit_cell')
 
            for name, variable in rootgrp.variables.items():
                if variable.dtype.char == 'S':
                    data = ''.join(variable[:]).decode('utf-8').strip()
                    f.attrs[name] = data
                else:
                    if name in chemical_system_vars:
                        group = chemical_system_grp
                    elif name in configuration_vars:
                        group = configuration_grp
                    elif name in unit_cell_vars:
                        group = unit_cell_grp
                    else:
                        group = f.create_group(name)
                    dataset = group.create_dataset(name, data=variable[:])
                    for attr_name in variable.ncattrs():
                        dataset.attrs[attr_name] = variable.getncattr(attr_name)
        print("Conversion successful. HDF5 file saved as: ", output_file)
    except Exception as e:
        print("An error occurred during the conversion: ", str(e))
 
if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "current_traj.nc"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output_file.h5"
    convert_netcdf_to_hdf5_mdanse(input_file, output_file)