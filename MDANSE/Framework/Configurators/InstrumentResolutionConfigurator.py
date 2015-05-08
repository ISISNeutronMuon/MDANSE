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

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class InstrumentResolutionConfigurator(IConfigurator):
    """
    This configurator allows to set an instrument resolution.
    
    The instrument resolution will be used in frequency-dependant analysis (e.g. the vibrational density 
    of states) when performing the fourier transform of its time-dependant counterpart. This allow to 
    convolute of the signal with a resolution function to have a better match with experimental spectrum.
    
    In MDANSE, the instrument resolution are defined in frequency (energy) space and are internally 
    inverse-fourier-transformed to get a time-dependant version. This time-dependant resolution function will then 
    be multiplied by the time-dependant signal to get the resolution effect according to the Fourier Transform theorem:
    
    .. math:: TF(f(t) * r(t)) = F(\omega) \conv R(\omega) = G(\omega)

    where f(t) and r(t) are respectively the time-dependant signal and instrument resolution and 
    F(\omega) and R(\omega) are their corresponding spectrum. Hence, G(\omega) represents the signal 
    convoluted by the instrument resolution and, as such, represents the quantity to be compared directly with 
    experimental results. 
    
    An instrument resolution is represented in MDANSE by a kernel function and a sets of parameters for this function.
    MDANSE currently supports the aussian, lorentzian, square, triangular and pseudo-voigt kernels.
    
    :note: this configurator depends on the 'frame' configurator to be configured
    """
    
    
    type = "instrument_resolution"
        
    _default = ('gaussian', {'mu': 0.0, 'sigma': 0.0001})
        
    def configure(self, configuration, value):
        '''
        Configure the instrument resolution.
                
        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the instrument resolution. It must be input as a 2-tuple where the 1st element is the instrument resolution
        kernel and the 2nd element is a dictionary that stores the parameters for this kernel.
        is a string representing one of the supported instrument resolution 
        :type value: 2-tuple
        '''

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
        
        self["kernel"] = kernel
        self["parameters"] = parameters
        
    def get_information(self):
        '''
        Returns some informations the instrument resolution.
        
        :return: the information the instrument resolution.
        :rtype: str
        '''
        
        if not self.has_key("kernel"):
            return "No configured yet"
        
        info = ["Instrument resolution kernel:" % self["kernel"]]
        if self["parameters"]:
            info.append("Parameters:")
            for k,v in self["parameters"]:
                info.append("%s = %s" % (k,v))
                
        info = "\n".join(info)
                    
        return info