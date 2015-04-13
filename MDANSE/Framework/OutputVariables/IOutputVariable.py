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

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

class OutputVariableError(Error):
    pass

class OutputData(collections.OrderedDict):
    
    def __setitem__(self,item):
        pass
    
    def add(self, dataName, dataType, data, **kwargs):
        
        self[dataName] = REGISTRY["output_variable"][dataType](data, dataName, **kwargs)
    
    def write(self, basename, formats, header=None):
        
        for fmt in formats:  
            REGISTRY["format"][fmt].write(basename, self, header)

class IOutputVariable(numpy.ndarray):
    '''
    Defines a MDANSE output variable.
    
    A MDANSE output variable is defined as s subclass of Numpy array that stores additional attributes.
    Those extra attributes will be contain information necessary for the the MDANSE plotter. 
    '''

    __metaclass__ = REGISTRY
    
    type = "output_variable"
        
    def __new__(cls, value, name, axis=(), units="unitless"):
        '''
        Instanciate a new MDANSE output variable.
                
        @param cls: the class to instantiate.
        @type cls: an OutputVariable object
        
        @param name: the name of the output variable.
        @type name: string
        
        @param value: the input numpy array.
        @type value: numpy array
        
        @note: This is the standard implementation for subclassing a numpy array.
        Please look at http://docs.scipy.org/doc/numpy/user/basics.subclassing.html for more information.
        '''
        
        if isinstance(value, tuple):
            value = numpy.zeros(value, dtype=numpy.float64)
        else:        
            value = numpy.array(value, dtype=numpy.float64)
            
        if value.ndim != cls._nDimensions:
            raise OutputVariableError("Invalid number of dimensions for an output variable of type %r" % cls.name)

        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = numpy.asarray(value).view(cls)
                                                        
        # The name of the output variable.               
        obj.name = name
                        
        obj.units = units

        obj.axis = axis
                                                        
        return obj
                
    def __array_finalize__(self, obj):
        
        if obj is None:
            return
                
        self.name = getattr(obj, 'name', None)
    
        self.axis = getattr(obj, 'axis',())

        self.units = getattr(obj, 'units','unitless')

    def __array_wrap__(self, out_arr, context=None):

        return numpy.ndarray.__array_wrap__(self, out_arr, context)
        
    def info(self):
        
        info = []

        info.append("# variable name: %s"  % self.name)
        info.append("# \ttype: %s"  % self.type)
        info.append("# \taxis: %s" % str(self.axis))
        info.append("# \tunits: %s" % self.units)
        
        info = "\n".join(info)
        
        return info
