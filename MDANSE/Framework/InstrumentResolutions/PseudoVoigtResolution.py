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

import collections

import numpy

from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import IInstrumentResolution

class PseudoVoigtInstrumentResolution(IInstrumentResolution):
    """Defines an instrument resolution with a pseudo-voigt response
    """

    type = 'pseudo-voigt'

    settings = collections.OrderedDict()
    settings['eta'] = ('float', {"mini":0.0, "maxi":1.0, "default":0.5})
    settings['mu_lorentzian'] = ('float', {"default":0.0})
    settings['sigma_lorentzian'] = ('float', {"default":1.0})
    settings['mu_gaussian'] = ('float', {"default":0.0})
    settings['sigma_gaussian'] = ('float', {"default":1.0})

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
