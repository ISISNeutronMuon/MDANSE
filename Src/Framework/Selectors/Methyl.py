# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/Methyl.py
# @brief     Implements module/class/test Methyl
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class Methyl(ISelector):

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the methyl atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():
            carbons = [at for at in obj.atomList() if at.type.name.strip().lower() == 'carbon']
            for car in carbons:
                neighbours = car.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                if len(hydrogens) == 3:
                    sel.update([car] + hydrogens)

        return sel

REGISTRY["methyl"] = Methyl
