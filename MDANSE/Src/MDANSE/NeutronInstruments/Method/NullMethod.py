# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/Method/NullMethod.py
# @brief     Elastic scattering, time of flight method
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************


from MDANSE.NeutronInstruments.Method.ScatteringMethod import ScatteringMethod


class NullMethod(ScatteringMethod):
    def apply_resolution(self):
        pass
