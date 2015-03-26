'''
MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
------------------------------------------------------------------------------------------
Copyright (C)
2015- Eric C. Pellegrini Institut Laue-Langevin
BP 156
6, rue Jules Horowitz
38042 Grenoble Cedex 9
France
pellegrini[at]ill.fr

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 
Created on Mar 23, 2015

@author: pellegrini
'''

import abc

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Configurables.Configurable import Configurable
from MDANSE.Framework.Configurables.Configurators import ConfiguratorsDict
from MDANSE.Core.Error import Error

class InstrumentResolutionError(Error):
    pass

class InstrumentResolution(Configurable):

    __metaclass__ = REGISTRY
    
    type = "instrument resolution"
    
    def __init__(self):
        
        Configurable.__init__(self)
                        
        self._frequencyWindow = None

        self._timeWindow = None
        
    @abc.abstractmethod
    def set_kernel(self, frequencies, dt, parameters=None):
        pass    
    
    @property
    def frequencyWindow(self):
        
        if self._frequencyWindow is None:
            raise InstrumentResolutionError("Undefined frequency window")
        
        return self._frequencyWindow

    @property
    def timeWindow(self):
        
        if self._timeWindow is None:
            raise InstrumentResolutionError("Undefined time window")
        
        return self._timeWindow

class IdealInstrumentResolution(InstrumentResolution):
    """Defines an ideal instrument resolution with a Dirac response 
    """
    
    type = 'ideal'
    
    configurators = ConfiguratorsDict()

    __doc__ += configurators.build_doc()

    def set_kernel(self, frequencies, dt):
                
        self._frequencyWindow = numpy.zeros(len(frequencies), dtype=numpy.float64)
        self._frequencyWindow[len(frequencies)/2] = 1.0

        self._timeWindow = numpy.ones(len(frequencies), dtype=numpy.float64)

class GaussianInstrumentResolution(InstrumentResolution):
    """Defines an instrument resolution with a gaussian response
    """
    
    type = 'gaussian'

    configurators = ConfiguratorsDict()
    configurators.add_item('mu', 'float', default=0.0)
    configurators.add_item('sigma', 'float', default=1.0)

    __doc__ += configurators.build_doc()
                
    def set_kernel(self, frequencies, dt):

        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]
        
        self._frequencyWindow = (1.0/(sigma*numpy.sqrt(2.0*numpy.pi)))*numpy.exp(-0.5*((frequencies-mu)/sigma)**2)
        self._timeWindow = numpy.fft.fftshift(numpy.abs(numpy.fft.ifft(self._frequencyWindow))/dt)
                 
class LorentzianInstrumentResolution(InstrumentResolution):
    """
    Defines an instrument resolution with a lorentzian response
    """
    
    type = 'lorentzian'

    configurators = ConfiguratorsDict()
    configurators.add_item('mu', 'float', default=0.0)
    configurators.add_item('sigma', 'float', default=1.0)

    __doc__ += configurators.build_doc()

    def set_kernel(self, frequencies, dt):

        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]
                
        fact = 0.5*sigma
                          
        self._frequencyWindow = (1.0/numpy.pi)*(fact/((frequencies-mu)**2 + fact**2))
                
        self._timeWindow = numpy.fft.fftshift(numpy.abs(numpy.fft.ifft(self._frequencyWindow))/dt)

class PseudoVoigtInstrumentResolution(InstrumentResolution):
    """Defines an instrument resolution with a pseudo-voigt response
    """

    type = 'pseudo-voigt'

    configurators = ConfiguratorsDict()
    configurators.add_item('eta','float', mini=0.0, maxi=1.0, default=0.5)
    configurators.add_item('mu_lorentzian','float', default=0.0)
    configurators.add_item('sigma_lorentzian','float', default=1.0)
    configurators.add_item('mu_gaussian','float', default=0.0)
    configurators.add_item('sigma_gaussian','float', default=1.0)

    __doc__ += configurators.build_doc()
            
    def set_kernel(self, frequencies, dt):

        eta = self._configuration["eta"]["value"]
        muL = self._configuration["mu_lorentzian"]["value"]
        sigmaL = self._configuration["sigma_lorentzian"]["value"]
        muG = self._configuration["mu_gaussian"]["value"]
        sigmaG = self._configuration["sigma_gaussian"]["value"]

        gContribution = (1.0/(sigmaG*numpy.sqrt(2.0*numpy.pi)))*numpy.exp(-0.5*((frequencies-muG)/sigmaG)**2)

        fact = 0.5*sigmaL
                          
        lContribution = (1.0/numpy.pi)*(fact/((frequencies-muL)**2 + fact**2))
        
        self._frequencyWindow = eta*lContribution + (1.0-eta)*gContribution
                
        self._timeWindow = numpy.fft.fftshift(numpy.abs(numpy.fft.ifft(self._frequencyWindow))/dt)
        
class TriangularInstrumentResolution(InstrumentResolution):
    """Defines an instrument resolution with a triangular response
    """
    
    type = 'triangular'

    configurators = ConfiguratorsDict()
    configurators.add_item('mu', 'float', default=0.0)
    configurators.add_item('sigma', 'float', default=1.0)

    __doc__ += configurators.build_doc()
    
    def set_kernel(self, frequencies, dt):

        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]
                                
        val = numpy.abs(frequencies-mu) - sigma
                        
        self._frequencyWindow = numpy.where( val >= 0, 0.0, -val/sigma**2)
                                
        self._timeWindow = numpy.fft.fftshift(numpy.abs(numpy.fft.ifft(self._frequencyWindow))/dt)

class SquareInstrumentResolution(InstrumentResolution):
    """Defines an instrument resolution with a square response
    """
    
    type = 'square'

    configurators = ConfiguratorsDict()
    configurators.add_item('mu', 'float', default=0.0)
    configurators.add_item('sigma', 'float', default=1.0)

    __doc__ += configurators.build_doc()
        
    def set_kernel(self, frequencies, dt):
                                
        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]
                                
        self._frequencyWindow = numpy.where((numpy.abs(frequencies-mu)-sigma) > 0,0.0,1.0/(2.0*sigma))
                        
        self._timeWindow = numpy.fft.fftshift(numpy.abs(numpy.fft.ifft(self._frequencyWindow))/dt)

if __name__ == "__main__":
    
    res = REGISTRY["instrument resolution"]["square"]()
    res.setup({"mu":2.0,"sigma":1.0})
    res.set_kernel(numpy.array([1,2,3,4,5,6,7,8]),0.1)
