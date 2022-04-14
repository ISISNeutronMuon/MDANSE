# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/McStasParametersConfigurator.py
# @brief     Implements module/class/test McStasParametersConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import re
import subprocess

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
        
class McStasParametersConfigurator(IConfigurator):
    '''
    This configurator allows to input the McStas instrument parameters that will be used to run a McStas executable file.
    '''

    _mcStasTypes = {'double' : float, 'int' : int, 'string' : str}

    _default = {'beam_wavelength_Angs': 2.0,
                'environment_thickness_m': 0.002,
                'beam_resolution_meV': 0.1,
                'container':os.path.join(PLATFORM.example_data_directory(),'McStas','Samples','Al.laz'),
                'container_thickness_m': 5e-05,
                'sample_height_m': 0.05,
                'environment':os.path.join(PLATFORM.example_data_directory(),'McStas','Samples','Al.laz'),
                'environment_radius_m': 0.025,
                'sample_thickness_m': 0.001,
                'sample_detector_distance_m': 4.0,
                'sample_width_m': 0.02,
                'sample_rotation_deg': 45.0,
                'detector_height_m': 3.0}        
    
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
        
    def configure(self, value):
        '''
        Configure the McStas instrument parameters command line. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the McStas instrument parameters. 
        :type value: dict        
        '''
        
        instrConfig = self._configurable[self._dependencies['instrument']]
        
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

REGISTRY["mcstas_parameters"] = McStasParametersConfigurator
