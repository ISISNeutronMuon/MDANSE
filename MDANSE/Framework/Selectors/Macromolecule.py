#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 27, 2015

:author: Eric C. Pellegrini
'''

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
