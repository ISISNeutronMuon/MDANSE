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

from MDANSE.Framework.Configurators.RangeConfigurator import RangeConfigurator

class FramesConfigurator(RangeConfigurator):
    """
    This configurator allows to input a frame selection for the analysis.
    
    The frame selection can be input as:
    
    #. a 3-tuple where the 1st, 2nd will corresponds respectively to the indexes of the first and \
    last (excluded) frames to be selected while the 3rd element will correspond to the step number between two frames. For example (1,11,3) will give 1,4,7,10
    #. *'all'* keyword, in such case, all the frames of the trajectory are selected
    #. ``None`` keyword, in such case, all the frames of the trajectory are selected

    :note: this configurator depends on 'trajectory' configurator to be configured
    """
    
    type = 'frames'
    
    def __init__(self, name, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        '''

        RangeConfigurator.__init__(self, name, sort=True, **kwargs)
             
    def configure(self, configuration, value):
        '''
        Configure the frames range that will be used to perform an analysis.
                
        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input value
        :type value: 3-tuple, 'all' or None
        '''
                                        
        trajConfig = configuration[self._dependencies['trajectory']]

        if value in ["all",None]:
            value = (0, trajConfig['length'], 1)
            
        self._mini = -1
        self._maxi = trajConfig['length']
        
        RangeConfigurator.configure(self, configuration, value)
                                                          
        self["n_frames"] = self["number"]
                                                                                             
        self['time'] = trajConfig['md_time_step']*self['value']

        self['relative_time'] = self['time'] - self['time'][0]
        
        # case of single frame selected
        try:
            self['time_step'] = self['time'][1] - self['time'][0]
        except IndexError:
            self['time_step'] = 1.0

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "%d frames selected (first=%.3f ; last = %.3f ; time step = %.3f)" % \
            (self["n_frames"],self["time"][0],self["time"][-1],self["time_step"])