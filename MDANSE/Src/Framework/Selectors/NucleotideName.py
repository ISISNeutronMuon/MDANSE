# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/NucleotideName.py
# @brief     Implements module/class/test NucleotideName
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import NucleotideChain, ChemicalSystem
from MDANSE.Framework.Selectors.ISelector import ISelector


class NucleotideName(ISelector):
    section = "nucleic acids"

    def __init__(self, chemicalSystem: ChemicalSystem):

        ISelector.__init__(self,chemicalSystem)

        for ce in self._chemicalSystem.chemical_entities:
            if isinstance(ce, NucleotideChain):
                self._choices.extend([n.name for n in ce.nucleotides])

    def select(self, names):
        """Returns the atoms that matches a given list of nucleotide names.

        @param names: the nucletodide names list.
        @type names: list
        """

        sel = set()

        if "*" in names:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, NucleotideChain):
                    sel.update([at for at in ce.atom_list])
        
        else:
            vals = set([v for v in names])

            for ce in self._chemicalSystem.chemical_entities:
                try:
                    for nucl in ce.nucleotides:
                        if nucl.name in vals:
                            sel.update([at for at in nucl.atom_list])
                except AttributeError:
                    pass

        return sel


REGISTRY["nucleotide_name"] = NucleotideName
