# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/__init__.py
# @brief     Implements __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

from MDANSE.NeutronInstruments.NeutronInstrument import NeutronInstrument
from MDANSE.NeutronInstruments.Coverage.Coverage import Coverage
from MDANSE.NeutronInstruments.Resolution.Resolution import Resolution
from MDANSE.NeutronInstruments.Spectrum.Spectrum import Spectrum


class IdealInstrument(NeutronInstrument):
    def __init__(self, *args, **kwargs):
        self.coverage = Coverage.create("TotalCoverage")
        self.spectrum = Spectrum.create("FlatSpectrum")
        self.resolution = Resolution.create("IdealResolution")
