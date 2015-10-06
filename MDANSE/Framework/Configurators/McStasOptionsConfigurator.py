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

:author: Eric C. Pellegrini
'''

import os
import tempfile
import time

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class McStasOptionsConfigurator(IConfigurator):
    """
    This configurator allows to input the McStas options that will be used to run a McStas executable file.
    """

    type = "mcstas_options"
    
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