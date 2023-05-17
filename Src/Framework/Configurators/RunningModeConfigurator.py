# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/RunningModeConfigurator.py
# @brief     Implements module/class/test RunningModeConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
                        
class RunningModeConfigurator(IConfigurator):
    """
    This configurator allows to choose the mode used to run the calculation.
    
    MDANSE currently support monoprocessor or multiprocessor (SMP) running modes. In the laster case, you have to 
    specify the number of slots used for running the analysis.
    """
    
    availablesModes = ["monoprocessor","multiprocessor"]
    
    _default = ("monoprocessor", 1)                

    def configure(self, value):
        '''
        Configure the running mode.
     
        :param value: the running mode specification. It can be *'monoprocessor'* or a 2-tuple whose first element \
        must be *'multiprocessor'* and 2nd element the number of slots allocated for running the analysis.
        :type value: *'monoprocessor'* or 2-tuple
        '''
                
        if isinstance(value,str):
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
    
REGISTRY['running_mode'] = RunningModeConfigurator
