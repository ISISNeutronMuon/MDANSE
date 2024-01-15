# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/Macromolecule.py
# @brief     Implements module/class/test Macromolecule
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE.Chemistry.ChemicalEntity import (
    NucleotideChain,
    PeptideChain,
    Protein,
    ChemicalSystem,
)
from MDANSE.Framework.Selectors.ISelector import ISelector


class Macromolecule(ISelector):
    section = "miscellaneous"

    lookup = {
        NucleotideChain: "nucleotide_chain",
        PeptideChain: "peptide_chain",
        Protein: "protein",
    }

    def __init__(self, chemicalSystem: ChemicalSystem):
        ISelector.__init__(self, chemicalSystem)

        self._choices.extend(["peptide_chain", "protein", "nucleotide_chain"])

    def select(self, macromolecules):
        """Return the macromolecules.

        @param classes: the residue classes list.
        @type classes: list
        """

        sel = set()

        if "*" in macromolecules:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (NucleotideChain, PeptideChain, Protein)):
                    sel.update([at for at in ce.atom_list])

        else:
            for ce in self._chemicalSystem.chemical_entities:
                m = Macromolecule.lookup.get(ce.__class__, None)
                if m in macromolecules:
                    sel.update([at for at in ce.atom_list])
                if (isinstance(ce, Protein)
                        and "peptide_chain" in macromolecules):
                    for ce2 in ce.peptide_chains:
                        m = Macromolecule.lookup.get(ce2.__class__, None)
                        if m in macromolecules:
                            sel.update([at for at in ce.atom_list])

        return sel
