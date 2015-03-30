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
Created on Mar 30, 2015

@author: pellegrini
'''

import numpy

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
        
class RangeConfigurator(IConfigurator):
    """
    This configurator allow to input a range of value given 3 parameters : start, stop, step
    """
    
    type = "range"

    _default = (0,10,1)

    def __init__(self, name, valueType=int, includeLast=False, sort=False, toList=False, mini=None, maxi=None, **kwargs):
                        
        IConfigurator.__init__(self, name, **kwargs)
        
        self._valueType = valueType
        
        self._includeLast = includeLast
        
        self._sort = sort
        
        self._toList = toList
        
        self._mini = mini
        
        self._maxi = maxi
                        
    def configure(self, configuration, value):
        
        first, last, step = value
        
        if self._includeLast:
            last += step/2.0
            
        value = numpy.arange(first, last, step)
        value = value.astype(self._valueType)
        
        if self._mini is not None:
            value = value[value >= self._mini]

        if self._maxi is not None:
            value = value[value <= self._maxi]
        
        if value.size == 0:
            raise ConfiguratorError("the input range is empty." , self)
        
        if self._sort:
            value = numpy.sort(value)
        
        if self._toList:
            value = value.tolist()
                                                             
        self["value"] = value
        
        self['first'] = self['value'][0]
                
        self['last'] = self['value'][-1]

        self['number'] = len(self['value'])
                
        self['mid_points'] = (value[1:]+value[0:-1])/2.0

        try:
            self["step"] = self['value'][1] - self['value'][0]
        except IndexError:
            self["step"] = 1
                    
    @property
    def valueType(self):
        
        return self._valueType
    
    @property
    def includeLast(self):
        
        return self._includeLast
    
    @property
    def toList(self):
        
        return self._toList
    
    @property
    def sort(self):
        
        return self._sort
    
    @property
    def mini(self):
        
        return self._mini   
    
    @property
    def maxi(self):
        
        return self._maxi   

    def get_information(self):
        
        info = "$d values from %s to %s" % (self['number'],self['first'],self['last'])
        
        if self._includeLast:
            info += ("last value included")
        else:
            info += ("last value excluded")
         
        return info