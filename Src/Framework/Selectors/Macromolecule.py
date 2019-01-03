from MMTK.NucleicAcids import NucleotideChain
from MMTK.Proteins import PeptideChain, Protein

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class Macromolecule(ISelector):
        
    section = "miscellaneous"
    
    lookup = {NucleotideChain:"nucleotide_chain",PeptideChain:"peptide_chain",Protein:"protein"}

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        self._choices.extend(["peptide_chain","protein","nucleotide_chain"])
         
    def select(self, macromolecules):
        '''
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param classes: the residue classes list.
        @type classes: list
        '''
                                
        sel = set()

        if '*' in macromolecules:
            for obj in self._universe.objectList():
                if isinstance(obj, (NucleotideChain,PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:
            for obj in self._universe.objectList():
                m = Macromolecule.lookup.get(obj.__class__,None)
                if m in macromolecules:
                    sel.update([at for at in obj.atomList()])

        return sel

REGISTRY["macromolecule"] = Macromolecule
