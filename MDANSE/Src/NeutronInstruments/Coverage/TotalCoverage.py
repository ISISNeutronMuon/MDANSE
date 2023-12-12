# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/Coverage/TotalCoverage.py
# @brief     A Null coverage: every angle covered
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

from MDANSE.NeutronInstruments.Coverage.Coverage import Coverage


class TotalCoverage(Coverage):
    def in_range(self, phi: float, theta: float):
        return True
