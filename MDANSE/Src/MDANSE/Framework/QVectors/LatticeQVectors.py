# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/LatticeQvectors.py
# @brief     Implements module/class/test LatticeQvectors
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy as np

from MDANSE.Framework.QVectors.IQVectors import IQVectors, QVectorsError


class LatticeQVectors(IQVectors):
    is_lattice = True

    def __init__(self, chemical_system, status=None):
        super(LatticeQVectors, self).__init__(chemical_system, status)

        if self._chemical_system.configuration is None:
            raise QVectorsError("No configuration set for the chemical system")

        if not self._chemical_system.configuration.is_periodic:
            raise QVectorsError(
                "The universe must be periodic for building lattice-based Q vectors"
            )

        self._inverseUnitCell = (
            2.0 * np.pi * self._chemical_system.configuration.unit_cell.inverse
        )

        self._directUnitCell = (
            2.0 * np.pi * self._chemical_system.configuration.unit_cell.direct
        )
