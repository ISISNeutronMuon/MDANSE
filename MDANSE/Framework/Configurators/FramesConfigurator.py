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

from MDANSE.Framework.Configurators.RangeConfigurator import RangeConfigurator

class FramesConfigurator(RangeConfigurator):
    """
    This frames configurator allow to select as input of the analysis a range of frame 
    given 3 parameters : the first frame, the last frame, and the value of the step 
    """
    
    type = 'frames'
    
    def __init__(self, name, **kwargs):

        RangeConfigurator.__init__(self, name, sort=True, **kwargs)
             
    def configure(self, configuration, value):
                                        
        trajConfig = configuration[self._dependencies['trajectory']]

        if value == "all":
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
        
        return "%d frames selected (first=%.3f ; last = %.3f ; time step = %.3f)" % \
            (self["n_frames"],self["time"][0],self["time"][-1],self["time_step"])