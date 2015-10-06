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
Created on May 22, 2015

:author: Eric C. Pellegrini
'''

from MDANSE import ELEMENTS
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import SingleChoiceConfigurator

class WeightsConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to select how the properties that depends on atom type will be weighted when computing
    the total contribution of all atoms.
    
    Any numeric property defined in MDANSE.Data.ElementsDatabase.ElementsDatabase can be used as a weigh.
    """
    
    type = 'weights'
    
    _default = "equal"
           
    def __init__(self, name, **kwargs):
        '''
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        '''
                
        SingleChoiceConfigurator.__init__(self, name, choices=ELEMENTS.numericProperties, **kwargs)

    def configure(self, value):
        '''
        Configure the weight.
                
        :param value: the name of the weight to use.
        :type value: one of the numeric properties of MDANSE.Data.ElementsDatabase.ElementsDatabase
        '''
        
        if not isinstance(value,basestring):
            raise ConfiguratorError("Invalid type for weight. Must be a string.", self)
        
        value = value.lower()
        
        if not value in ELEMENTS.numericProperties:
            raise ConfiguratorError("weight %r is not registered as a valid numeric property." % value, self)
                                         
        self['property'] = value

    def get_weights(self):
        
        ascfg = self._configurable[self._dependencies['atom_selection']]

        weights = {}
        for i in range(ascfg["selection_length"]):
            name = ascfg["names"][i]
            for el in ascfg["elements"][i]:
                p = ELEMENTS[el,self["property"]]
                if weights.has_key(name):
                    weights[name] += p
                else:
                    weights[name] = p
                    
        for k,v in ascfg.get_natoms().items():
            weights[k] /= v
            
        return weights

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "selected weight: %s" % self["property"]