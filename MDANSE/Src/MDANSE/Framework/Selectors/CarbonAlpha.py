# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/CarbonAlpha.py
# @brief     Implements module/class/test CarbonAlpha
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE.Framework.Selectors.ISelector import ISelector


class CarbonAlpha(ISelector):
    section = "proteins"

    def select(self, *args):
        """Returns the c_alpha atoms.

        Only for Protein and PeptideChain objects.
        """

        sel = set()

        for ce in self._chemicalSystem.chemical_entities:
            try:
                sel.update([at for at in ce.atom_list if at.name.strip() == "CA"])
            except AttributeError:
                pass

        return sel
