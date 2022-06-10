# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/OutputVariables/IOutputVariable.py
# @brief     Implements module/class/test IOutputVariable
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

class OutputVariableError(Error):
    pass

class OutputData(collections.OrderedDict):
    
    def add(self, dataName, dataType, data, **kwargs):
                
        collections.OrderedDict.__setitem__(self,dataName,REGISTRY["output_variable"][dataType](data, dataName, **kwargs))
    
    def write(self, basename, formats, header=None):
        
        for fmt in formats:  
            REGISTRY["format"][fmt].write(basename, self, header)

class IOutputVariable(numpy.ndarray):
    '''
    Defines a MDANSE output variable.
    
    A MDANSE output variable is defined as s subclass of Numpy array that stores additional attributes.
    Those extra attributes will be contain information necessary for the the MDANSE plotter. 
    '''
    
    _registry = "output_variable"
        
    def __new__(cls, value, varname, axis='index', units="unitless"):
        '''
        Instanciate a new MDANSE output variable.
                
        @param cls: the class to instantiate.
        @type cls: an OutputVariable object
        
        @param varname: the name of the output variable.
        @type varname: string
        
        @param value: the input numpy array.
        @type value: numpy array
        
        @note: This is the standard implementation for subclassing a numpy array.
        Please look at http://docs.scipy.org/doc/numpy/user/basics.subclassing.html for more information.
        '''
        
        if isinstance(value, tuple):
            value = numpy.zeros(value, dtype=numpy.float64)
        else:        
            value = numpy.array(list(value), dtype=numpy.float64)
            
        if value.ndim != cls._nDimensions:
            raise OutputVariableError("Invalid number of dimensions for an output variable of type %r" % cls.name)

        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = numpy.asarray(value).view(cls)
                                                        
        # The name of the output variable.               
        obj.varname = varname
                        
        obj.units = units

        obj.axis = axis
                                                        
        return obj
                
    def __array_finalize__(self, obj):
        
        if obj is None:
            return
                
        self.varname = getattr(obj, 'varname', None)
    
        self.axis = getattr(obj, 'axis',())

        self.units = getattr(obj, 'units','unitless')

    def __array_wrap__(self, out_arr, context=None):

        return numpy.ndarray.__array_wrap__(self, out_arr, context)
        
    def info(self):
        
        info = []

        info.append("# variable name: %s"  % self.varname)
        info.append("# \ttype: %s"  % self._type)
        info.append("# \taxis: %s" % str(self.axis))
        info.append("# \tunits: %s" % self.units)
        
        info = "\n".join(info)
        
        return info
