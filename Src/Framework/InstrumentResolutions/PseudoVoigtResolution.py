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

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import IInstrumentResolution

class PseudoVoigtInstrumentResolution(IInstrumentResolution):
    """Defines an instrument resolution with a pseudo-voigt response
    """

    settings = collections.OrderedDict()
    settings['eta'] = ('float', {"mini":0.0, "maxi":1.0, "default":0.5})
    settings['mu_lorentzian'] = ('float', {"default":0.0})
    settings['sigma_lorentzian'] = ('float', {"default":1.0})
    settings['mu_gaussian'] = ('float', {"default":0.0})
    settings['sigma_gaussian'] = ('float', {"default":1.0})

    def set_kernel(self, omegas, dt):

        eta = self._configuration["eta"]["value"]
        muL = self._configuration["mu_lorentzian"]["value"]
        sigmaL = self._configuration["sigma_lorentzian"]["value"]
        muG = self._configuration["mu_gaussian"]["value"]
        sigmaG = self._configuration["sigma_gaussian"]["value"]

        gaussian = (numpy.sqrt(2.0*numpy.pi)/sigmaG)*numpy.exp(-0.5*((omegas-muG)/sigmaG)**2)
                          
        lorentzian = (2.0*sigmaL)/((omegas-muL)**2 + sigmaL**2)
        
        self._omegaWindow = eta*lorentzian + (1.0-eta)*gaussian
        self._timeWindow = numpy.fft.fftshift(numpy.fft.ifft(numpy.fft.ifftshift(self._omegaWindow))/dt)

REGISTRY['pseudo-voigt'] = PseudoVoigtInstrumentResolution
                