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

import numpy

import netCDF4

from MDANSE import REGISTRY
from MDANSE.Framework.Formats.IFormat import IFormat

class NetCDFFormat(IFormat):
    '''
    This class handles the writing of output variables in NetCDF file format.
    '''

    extension = ".nc"
    
    extensions = ['.nc','.cdf','.netcdf']
    
    @classmethod
    def write(cls, filename, data, header=""):
        '''
        Write a set of output variables into a NetCDF file.
                
        :param filename: the path to the output NetCDF file.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        '''
                
        filename = os.path.splitext(filename)[0]

        filename = "%s%s" % (filename,cls.extensions[0])
       
        # The NetCDF output file is opened for writing.
        outputFile = netCDF4.Dataset(filename, 'w')
        
        if header:
            # This is to avoid any segmentation fault when writing the NetCDF header field
            header = str(header)

            outputFile.header = header
        
        # Loop over the OutputVariable instances to write.
        
        for var in data.values():
                                    
            varName = str(var.varname).strip().encode('string-escape').replace('/', '|')
            
            # The NetCDF dimensions are created for all the dimensions of the OutputVariable instance.
            dimensions = []
            for i,v in enumerate(var.shape):
                name = str("%s_%d" % (varName,i))
                dimensions.append(name)
                outputFile.createDimension(name, int(v))

            # A NetCDF variable instance is created for the running OutputVariable instance.        
            NETCDFVAR = outputFile.createVariable(varName, numpy.dtype(var.dtype).char, tuple(dimensions))

            # The array stored in the OutputVariable instance is written to the NetCDF file.
            NETCDFVAR[:] = var

            # All the attributes stored in the OutputVariable instance are written to the NetCDF file.
            for k, v in vars(var).items():
                setattr(NETCDFVAR,str(k),str(v))
        
        # The NetCDF file is closed.
        outputFile.close()

REGISTRY['netcdf'] = NetCDFFormat
