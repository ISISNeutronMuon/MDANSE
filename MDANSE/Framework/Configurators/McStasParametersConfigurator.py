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

@author: Eric C. Pellegrini
'''

import re
import subprocess

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
        
class McStasParametersConfigurator(IConfigurator):
    '''
    This configurator allows to input the McStas instrument parameters that will be used to run a McStas executable file.
    '''

    type = "instrument_parameters"

    _mcStasTypes = {'double' : float, 'int' : int, 'string' : str}
    
    def __init__(self, name, exclude=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param exclude: the parameters that exclude when building the McStas instrument parameters list.
        :type exclude: list of str
        '''
        
        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._exclude = exclude if exclude is not None else []
        
    def configure(self, configuration, value):
        '''
        Configure the McStas instrument parameters command line. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the McStas instrument parameters. 
        :type value: dict        
        '''
        
        instrConfig = configuration[self._dependencies['instrument']]
        
        exePath = instrConfig['value']
        
        s = subprocess.Popen([exePath,'-h'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
               
        instrParameters = dict([(v[0],[v[1],v[2]]) for v in re.findall("\s*(\w+)\s*\((\w+)\)\s*\[default=\'(\S+)\'\]",s.communicate()[0]) if v[0] not in self._exclude])
                
        val = {}
        for k,v in value.items():
            if k not in instrParameters:
                instrParameters.pop(k)
            val[k] = self._mcStasTypes[instrParameters[k][0]](v)
                                                      
        self["value"] = ["%s=%s" % (k,v) for k,v in val.items()]
        
    @property
    def exclude(self):
        '''
        Returns the McStas instrument parameters to exclude from the McStas command-line.
        
        :return: the McStas instrument parameters to exclude from the McStas command-line.
        :rtype: list of str
        '''
        
        return self._exclude

    def get_information(self):
        '''
        Returns the McStas parameters as they would be input when using McStas in command line mode.
        
        :return: the McStas command-line parameters.
        :rtype: str
        '''
        
        return "McStas command line parameters:%s" % self["value"]
