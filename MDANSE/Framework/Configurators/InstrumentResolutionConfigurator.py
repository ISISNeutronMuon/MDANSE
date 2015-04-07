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

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class InstrumentResolutionConfigurator(IConfigurator):
    """
    This configurator allow to set a simulated instrument resolution.
    Clicking on the SET button open a widget allowing to select one function into 
    a set of basics, and to parameterized it, then the resulting kernel will be 
    automatically sampled and convoluted with the signal.
    """
    
    type = "instrument_resolution"
        
    _default = ('gaussian', {'mu': 0.0, 'sigma': 0.0001})
        
    def configure(self, configuration, value):

        framesCfg = configuration[self._dependencies['frames']]
                
        time = framesCfg["time"]
        self["n_frames"] = len(time)                                                                                             

        self._timeStep = framesCfg['time'][1] - framesCfg['time'][0]
        self['time_step'] = self._timeStep
                
        self["frequencies"] = numpy.fft.fftshift(numpy.fft.fftfreq(2*self["n_frames"]-1,self["time_step"]))
        
        df = round(self["frequencies"][1] - self["frequencies"][0],3)
        
        self["n_frequencies"] = len(self["frequencies"])

        kernel, parameters = value
                
        kernelCls = REGISTRY["instrument_resolution"][kernel]
                
        resolution = kernelCls()
        
        resolution.setup(parameters)
        
        resolution.set_kernel(self["frequencies"], self["time_step"])

        dmax = resolution.timeWindow.max()-1
        
        if dmax > 0.1:
            raise ConfiguratorError('''the resolution function is too sharp for the available frequency step. 
You can change your resolution function settings to make it broader or use "ideal" kernel if you do not want to smooth your signal.
For a gaussian resolution function, this would correspond to a sigma at least equal to the frequency step (%s)''' % df,self)
        elif dmax < -0.1:
            raise ConfiguratorError('''the resolution function is too broad.
You should change your resolution function settings to make it sharper.''',self)
            
        self["frequency_window"] = resolution.frequencyWindow

        self["time_window"] = resolution.timeWindow
        
    def get_information(self):
        
        return "None yet" 