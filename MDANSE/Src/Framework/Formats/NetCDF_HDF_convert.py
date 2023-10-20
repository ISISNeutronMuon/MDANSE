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

def read_netcdf_header(file_path):
    with open(file_path, 'rb') as file:
        magic_number = file.read(4)
    return magic_number == b'\x43\x44\x46\x01'

def remove_null_chars(s):
    # Function to remove embedded NULL characters from a string
    return s.replace(b'\x00', b'')

def convert_netcdf_to_hdf5(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    file_list = os.listdir(input_folder)

    for file_name in file_list:
        if file_name.lower().endswith(".nc"):
            try:
                netcdf_file = os.path.join(input_folder, file_name)                
                hdf5_file = os.path.splitext(file_name)[0] + '.h5'                
                hdf5_file_path = os.path.join(output_folder, hdf5_file)
                print(f"NetCDF file path: {netcdf_file}")
                print(f"HDF5 file path: {hdf5_file_path}")
                if read_netcdf_header(netcdf_file):
                    print("Extracting data...")
                    with open(netcdf_file, 'rb') as nc_file:
                        data = remove_null_chars(nc_file.read())
                    with h5py.File(hdf5_file_path, 'w') as h5_file:
                        h5_file.create_dataset('data', data=data)
                    print(f"Converted {netcdf_file} to {hdf5_file_path}")
                else:
                    print(f"Error: {file_name} is not a valid netCDF file.")
            except Exception as e:
                print(f"Error converting {netcdf_file}: {e}")

 

if __name__ == "__main__":
    # Define the path to the input folder containing NetCDF files
    input_netcdf_folder = "C:/Users/ttr36747/Documents/MDANSE/MDANSE/Data/Trajectories/MMTK"
    # Define the path to the output folder for HDF5 files
    output_hdf5_folder = "C:/Users/ttr36747/Documents/MDANSE/MDANSE/Data/Trajectories/NEW"
    # Call the conversion function with the specified input and output folders
    convert_netcdf_to_hdf5(input_netcdf_folder, output_hdf5_folder)