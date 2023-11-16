# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/Spectrum/Spectrum.py
# @brief     Base class for neutron instrument spectrum
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

from MDANSE.NeutronInstruments.Spectrum.Spectrum import Spectrum


class FlatSpectrum(Spectrum):
    def flux_at_wavelength(self, wavelength: float):
        return 1.0
