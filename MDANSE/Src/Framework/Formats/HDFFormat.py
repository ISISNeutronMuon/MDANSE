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

import os

import h5py

from MDANSE import REGISTRY
from MDANSE.Framework.Formats.IFormat import IFormat

class HDFFormat(IFormat):
    '''
    This class handles the writing of output variables in HDF file format.
    '''

    extension = ".h5"
    
    extensions = ['.h5','.hdf']
    
    @classmethod
    def write(cls, filename, data, header=""):
        '''
        Write a set of output variables into a HDF file.
                
        :param filename: the path to the output HDF file.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        '''
                
        filename = os.path.splitext(filename)[0]

        filename = "%s%s" % (filename,cls.extensions[0])
       
        # The NetCDF output file is opened for writing.
        outputFile = h5py.File(filename, 'w')
        
        if header:
            # This is to avoid any segmentation fault when writing the NetCDF header field
            header = str(header)

            outputFile.attrs['header'] = header
        
        # Loop over the OutputVariable instances to write.
        
        for var in list(data.values()):
                                    
            varName = str(var.varname).strip().replace('/', '|')
            
            dset = outputFile.create_dataset(varName, data=var, shape=var.shape)

            # All the attributes stored in the OutputVariable instance are written to the NetCDF file.
            for k, v in list(vars(var).items()):
                dset.attrs[k] = v
        
        # The HDF file is closed.
        outputFile.close()

REGISTRY['hdf'] = HDFFormat