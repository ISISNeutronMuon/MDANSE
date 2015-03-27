'''
MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
------------------------------------------------------------------------------------------
Copyright (C)
2015- Eric C. Pellegrini Institut Laue-Langevin
BP 156
6, rue Jules Horowitz
38042 Grenoble Cedex 9
France
pellegrini[at]ill.fr

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 
Created on Mar 23, 2015

@author: pellegrini
'''

import abc
import os
import re
import StringIO
import tarfile

import numpy

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Externals.svgfig.svgfig import _hacks, Frame, Poly

_hacks["inkscape-text-vertical-shift"] = True

class FormatError(Error):
    pass

def format_unit_string(unitString):

    return re.sub('[%()]','',unitString)
           
class Format(object):
    '''
    This is the base class for nmoldyn data.
    '''
    
    __metaclass__ = REGISTRY
    
    type = "format"
    
    @abc.abstractmethod
    def write(self, filename, data, header=""):
        pass

            
class ASCIIFormat(Format):
    
    type = 'ascii'

    extension = ".dat"

    extensions = ['.dat','.txt']
    
    @classmethod
    def write(cls, filename, data, header=""):
                
        filename = os.path.splitext(filename)[0]
        filename = "%s_%s.tar" % (filename,cls.type)

        tf = tarfile.open(filename,'w')
        
        for var in data.values():

            tempStr = StringIO.StringIO()
            if header:
                tempStr.write(header)
                tempStr.write('\n\n')  
            tempStr.write(var.info())
            tempStr.write('\n\n')            
            cls.write_array(tempStr,var)
            tempStr.seek(0)

            info = tarfile.TarInfo(name='%s%s' % (var.name,cls.extensions[0]))
            info.size=tempStr.len
            tf.addfile(tarinfo=info, fileobj=tempStr)
                                    
        tf.close()

    @classmethod
    def write_array(cls, fileobject, array, slices=None):
        
        if slices is None:
            slices = [0]*array.ndim
            slices[-2:] = array.shape[-2:]

        if array.ndim > 2:
        
            for a in array:
                cls.write_array(fileobject,a, slices)
                slices[len(slices)-array.ndim] = slices[len(slices)-array.ndim] + 1

        else:
            fileobject.write('#slice:%s\n' % slices)
            numpy.savetxt(fileobject, array)
            fileobject.write('\n')


class NetCDFFormat(Format):

    type = 'netcdf'

    extension = ".nc"
    
    extensions = ['.nc','.cdf','.netcdf']
    
    @classmethod
    def write(cls, filename, data, header=""):
        '''
        This method writes (or append) a list of nMOLDYN.Job.Output.OutputVariable objects to a NetCDF file.
    
        @param filename: the path for the output NetCDF file.
        @type filename: string
        '''
                
        filename = os.path.splitext(filename)[0]

        filename = "%s%s" % (filename,cls.extensions[0])
       
        # Import the NetCDFFile function.
        from Scientific.IO.NetCDF import NetCDFFile

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

class SVGFormat(Format):

    type = 'svg'
    
    extension = ".svg"
    
    extensions = ['.svg']
        
    @classmethod
    def write(cls,filename,data, header=""):

        filename = os.path.splitext(filename)[0]
        filename = "%s.tar" % filename

        tf = tarfile.open(filename,'w')
                                
        for var in data.values():
                        
            if var.ndim != 1:
                continue
            
            if var.axis in data:
                axis = data[var.axis]
                xtitle = "%s (%s)" % (axis.name,format_unit_string(axis.units))
            else:
                axis = numpy.arange(len(var))
                xtitle = 'index'
                
            ytitle = "%s (%s)" % (var.name,format_unit_string(var.units))
                        
            pl = Poly(zip(axis,var),stroke='blue')

            svgfilename = os.path.join(os.path.dirname(filename),'%s%s' % (var.name,cls.extensions[0]))
            
            Frame(min(axis),max(axis),min(var),max(var),pl,xtitle=xtitle,ytitle=ytitle).SVG().save(svgfilename)

            tf.add(svgfilename, arcname='%s%s' % (var.name,cls.extensions[0]))
            
            os.remove(svgfilename)
    
        tf.close()
