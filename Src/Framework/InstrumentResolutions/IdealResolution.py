# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InstrumentResolutions/IdealResolution.py
# @brief     Implements module/class/test IdealResolution
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import IInstrumentResolution

class IdealInstrumentResolution(IInstrumentResolution):
    """Defines an ideal instrument resolution with a Dirac response 
    """
        
    settings = collections.OrderedDict()

    def set_kernel(self, omegas, dt):
                
        nOmegas = len(omegas)
        self._omegaWindow = numpy.zeros(nOmegas, dtype=numpy.float64)
        self._omegaWindow[nOmegas/2] = 1.0

        self._timeWindow = numpy.ones(nOmegas, dtype=numpy.float64)
        
REGISTRY['ideal'] = IdealInstrumentResolution
