# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/Resolution/IdealResolution.py
# @brief     Delta function resolution. No smearing, perfectly sharp.
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

import numpy as np

from MDANSE.NeutronInstruments.Resolution.Resolution import Resolution


class IdealResolution(Resolution):
    def resolution_window(self, energy_axis: np.ndarray, Ef: float, Ei: float):
        window_axis = np.linspace(0, energy_axis.max(), len(energy_axis))
        window_value = np.zeros_like(window_axis)
        window_value[0] = 1.0
        return window_value, window_axis
