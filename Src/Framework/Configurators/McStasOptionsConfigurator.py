# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/McStasOptionsConfigurator.py
# @brief     Implements module/class/test McStasOptionsConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import tempfile
import time

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class McStasOptionsConfigurator(IConfigurator):
    """
    This configurator allows to input the McStas options that will be used to run a McStas executable file.
    """
    
    _default = {"ncount" : 10000, "dir" : os.path.join(tempfile.gettempdir(),"mcstas_output",time.strftime("%d.%m.%Y-%H:%M:%S", time.localtime()))}
        
    def configure(self, value):
        '''
        Configure the McStas options. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the McStas options.
        :type value: dict
        '''
        
        options = self._default.copy()
        
        for k,v in value.items():
            if k not in options:
                continue
            options[k] = v
            
        tmp = ['']
        for k,v in options.items():     
            if k == "dir":
                # If the output directory already exists, defines a 'unique' output directory name because otherwise McStas throws.
                if os.path.exists(v):
                    v =  self._default['dir']
                self["mcstas_output_directory"] = v
            tmp.append("--%s=%s" % (k,v))

        dirname = os.path.dirname(self["mcstas_output_directory"])

        try:
            PLATFORM.create_directory(dirname)
        except:
            raise ConfiguratorError("The directory %r is not writable" % dirname)
                           
        self["value"] = tmp

    def get_information(self):
        '''
        Returns the McStas options as they would be input when using McStas in command line mode.
        
        :return: the McStas command-line options.
        :rtype: str
        '''
        
        return "McStas command line options: %s" % self["value"]
    
REGISTRY["mcstas_options"] = McStasOptionsConfigurator
