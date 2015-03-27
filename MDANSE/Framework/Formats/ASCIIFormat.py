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
import StringIO
import tarfile

import numpy

from MDANSE.Framework.Formats.IFormat import IFormat

class ASCIIFormat(IFormat):
    
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
