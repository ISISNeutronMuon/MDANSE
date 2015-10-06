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

import os

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
                        
class RunningModeConfigurator(IConfigurator):
    """
    This configurator allows to choose the mode used to run the calculation.
    
    MDANSE currently support monoprocessor or multiprocessor (SMP) running modes. In the laster case, you have to 
    specify the number of slots used for running the analysis.
    """

    type = 'running_mode'
    
    availablesModes = ["monoprocessor","multiprocessor"]
    
    _default = ("monoprocessor", 1)                

    def configure(self, value):
        '''
        Configure the running mode.
     
        :param value: the running mode specification. It can be *'monoprocessor'* or a 2-tuple whose first element \
        must be *'multiprocessor'* and 2nd element the number of slots allocated for running the analysis.
        :type value: *'monoprocessor'* or 2-tuple
        '''
                
        if isinstance(value,basestring):
            mode = value
        else:            
            mode = value[0].lower()
                    
        if not mode in self.availablesModes:
            raise ConfiguratorError("%r is not a valid running mode." % mode, self)

        if mode == "monoprocessor":
            slots = 1

        else:

            import Pyro

            Pyro.config.PYRO_STORAGE = PLATFORM.home_directory()
            Pyro.config.PYRO_NS_URIFILE = os.path.join(Pyro.config.PYRO_STORAGE,'Pyro_NS_URI')
            Pyro.config.PYRO_LOGFILE = os.path.join(Pyro.config.PYRO_STORAGE,'Pyro_log')
            Pyro.config.PYRO_USER_LOGFILE = os.path.join(Pyro.config.PYRO_STORAGE,'Pyro_userlog')
            Pyro.config.PYROSSL_CERTDIR = os.path.join(Pyro.config.PYRO_STORAGE,'certs')

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
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Run in %s mode (%d slots)" % (self["mode"],self["slots"])