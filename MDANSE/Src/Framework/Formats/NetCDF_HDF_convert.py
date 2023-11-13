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
import h5py
from netCDF4 import Dataset
from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
 
def convert_trajectory_to_hdf5(trajectory_filename, h5_filename):
    try:
        chemical_system = None
        with Dataset(trajectory_filename, 'r') as trajectory_file:
            chemical_entity_data = None
            for varname in trajectory_file.variables.keys():
                var = trajectory_file.variables[varname]
                if 'chemical_entity' in varname:
                    chemical_entity_data = var[:]
 
            with h5py.File(h5_filename, 'w') as h5_file:
                for dimname in trajectory_file.dimensions.keys():
                    dim = trajectory_file.dimensions[dimname]
                    h5_file.create_dataset(dimname, data=dim.size)
 
                for varname in trajectory_file.variables.keys():
                    var = trajectory_file.variables[varname]
                    if varname != 'chemical_entity':
                        h5_file.create_dataset(varname, data=var[:])
 
                if chemical_entity_data is not None:
                    atoms = []
                    for data in chemical_entity_data:
                        atom = Atom(*data)
                        atoms.append(atom)
                    chemical_system = ChemicalSystem(atoms) 
 
                    chemical_group = h5_file.create_group("ChemicalSystem")
                    for i, atom in enumerate(chemical_system.get_atoms()):
                        atom_group = chemical_group.create_group(f"Atom_{i}")
                        atom_group.create_dataset("element", data=atom.element)
                        atom_group.create_dataset("mass", data=atom.mass)
                        atom_group.create_dataset("position", data=atom.position)
 
                if chemical_system:
                    print(f"Converted {trajectory_filename} to {h5_filename} and stored chemical system information.")
                else:
                    print(f"Converted {trajectory_filename} to {h5_filename}")
 
    except Exception as e:
        print(f"Error converting {trajectory_filename} to HDF5: {e}")
 
# Example usage with the provided file paths
convert_trajectory_to_hdf5('C:/Users/ttr36747/Documents/MDANSE/MDANSE/Data/Trajectories/traj/current_traj.nc', 'C:/Users/ttr36747/Documents/MDANSE/MDANSE/Data/Trajectories/traj/new_trajectory.h5')