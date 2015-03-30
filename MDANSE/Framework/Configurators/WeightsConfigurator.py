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

from MDANSE import ELEMENTS
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import SingleChoiceConfigurator

class WeightsConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to choose the way the relevant quantities will be weighted during the calculation
    The most frequently used weights are defined as constant into the periodic table database.
    you can access to the table by clicking into the "atom" icon on the main toolbar
    """
    
    type = 'weights'
    
    _default = "equal"
           
    def __init__(self, name, choices=None, **kwargs):
        
        choices = choices if choices is not None else ELEMENTS.numericProperties
        
        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)

    def configure(self, configuration, value):
        
        value = value.lower()
        
        if not value in ELEMENTS.numericProperties:
            raise ConfiguratorError("weight %r is not registered as a valid numeric property." % value, self)
                                         
        self['property'] = value

    def get_information(self):
        
        return "Weighting scheme:%s" % self["property"]