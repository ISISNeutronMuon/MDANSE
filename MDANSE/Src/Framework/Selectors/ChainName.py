# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/ChainName.py
# @brief     Implements module/class/test ChainName
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import PeptideChain, Protein, ChemicalSystem
from MDANSE.Framework.Selectors.ISelector import ISelector


class ChainName(ISelector):
    section = "proteins"

    def __init__(self, chemicalSystem: ChemicalSystem):
        ISelector.__init__(self, chemicalSystem)

        for ce in self._chemicalSystem.chemical_entities:
            if isinstance(ce, (PeptideChain, Protein)):
                self._choices.extend([c.name for c in ce.peptide_chains])

    def select(self, names):
        """Returns the atoms that matches a given list of chain names.

        @param names: the chain names list.
        @type names: list
        """

        sel = set()

        if "*" in names:
            for ce in self._chemicalSystem.chemical_entities:
                try:
                    for pc in ce.peptide_chains:
                        sel.update([at for at in pc.atom_list])
                except AttributeError:
                    pass

        else:
            vals = set([v for v in names])

            for ce in self._chemicalSystem.chemical_entities:
                try:
                    for chain in ce.peptide_chains:
                        chainName = chain.name.strip()
                        if chainName in vals:
                            sel.update([at for at in chain.atom_list])
                except (AttributeError, TypeError):
                    continue

        return sel


REGISTRY["chain_name"] = ChainName
