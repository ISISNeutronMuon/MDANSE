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
Created on May 26, 2015

:author: Eric C. Pellegrini
'''

from MDANSE import REGISTRY

class IFormat(object):
    '''
    This is the base class for writing MDANSE output data. In MDANSE, the output of an analysis can be written in different file format.
    
    Currently, MDANSE supports NetCDF, SVG and ASCII output file formats. To introduce a new file output file format, just create a new concrete 
    subclass of IFormat and overload the "write" class method as defined in IFormat base class which will actually write the output variables, 
    and redefine the "type", "extension" and "extensions" class attributes.
    '''
    
    __metaclass__ = REGISTRY
    
    type = "format"

    @classmethod    
    def write(cls, filename, data, header=""):
        '''
        Write a set of output variables into filename using a given file format.
        
        :param filename: the path to the output file.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        '''
        
        pass
