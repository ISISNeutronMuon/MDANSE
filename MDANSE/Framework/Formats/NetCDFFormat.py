#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 27, 2015

@author: pellegrini
'''

import os

import numpy

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE.Framework.Formats.IFormat import IFormat

class NetCDFFormat(IFormat):

    type = 'netcdf'

    extension = ".nc"
    
    extensions = ['.nc','.cdf','.netcdf']
    
    @classmethod
    def write(cls, filename, data, header=""):
        '''
        This method writes (or append) a list of MDANSE.Job.Output.OutputVariable objects to a NetCDF file.
    
        @param filename: the path for the output NetCDF file.
        @type filename: string
        '''
                
        filename = os.path.splitext(filename)[0]

        filename = "%s%s" % (filename,cls.extensions[0])
       
        # The NetCDF output file is opened for writing.
        outputFile = NetCDFFile(filename, 'w')
        
        if header:
            outputFile.header = header
        
        # Loop over the OutputVariable instances to write.
        
        for var in data.values():
                                    
            varName = str(var.name).strip().encode('string-escape').replace('/', '|')
            
            # The NetCDF dimensions are created for all the dimensions of the OutputVariable instance.
            dimensions = []
            for i,v in enumerate(var.shape):
                name = str("%s_%d" % (varName,i))
                dimensions.append(name)
                outputFile.createDimension(name, int(v))

            # A NetCDF variable instance is created for the running OutputVariable instance.        
            NETCDFVAR = outputFile.createVariable(varName, numpy.dtype(var.dtype).char, tuple(dimensions))

            # The array stored in the OutputVariable instance is written to the NetCDF file.
            NETCDFVAR.assignValue(var)  

            # All the attributes stored in the OutputVariable instance are written to the NetCDF file.
            for k, v in vars(var).items():
                setattr(NETCDFVAR,str(k),str(v))
        
        # The NetCDF file is closed.
        outputFile.close()
