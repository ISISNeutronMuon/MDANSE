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

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
                        
class RunningModeConfigurator(IConfigurator):
    """
    This configurator allow to choose the mode use to run the calculation.
    choose among "monoprocessor" or "multiprocessor", 
    and also, in the second case, the number of processors getting involve.
    the option "remote", is not yet available.
    """

    type = 'running_mode'
    
    availablesModes = ["monoprocessor","multiprocessor","remote"]
    
    _default = ("monoprocessor", 1)                

    def configure(self, configuration, value):
                
        mode = value[0].lower()
        
        if not mode in self.availablesModes:
            raise ConfiguratorError("%r is not a valid running mode." % mode, self)

        if mode == "monoprocessor":
            slots = 1

        else:

            import Pyro
            Pyro.config.PYRO_STORAGE=PLATFORM.home_directory()

            slots = int(value[1])
                        
            if mode == "multiprocessor":
                import multiprocessing
                maxSlots = multiprocessing.cpu_count()
                del multiprocessing
                if slots > maxSlots:   
                    raise ConfiguratorError("invalid number of allocated slots.", self)
                      
            if slots <= 0:
                raise ConfiguratorError("invalid number of allocated slots.", self)
               
        self['mode'] = mode
        
        self['slots'] = slots

    def get_information(self):
        
        return "Run in %s mode (%d slots)" % (self["mode"],self["slots"])