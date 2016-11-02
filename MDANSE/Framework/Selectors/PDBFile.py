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

import os

from MMTK.PDB import PDBConfiguration

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector, SelectorError
                    
class PDBFile(ISelector):

    section = None

    def select(self, filename):
        '''
        Returns the atoms tagged in a given PDB file.

        @param universe: the universe
        @type universe: MMTK.universe
    
        @param filename: the PDB file.
        @type filename: string
        '''
        
        if not isinstance(filename,basestring):
            raise SelectorError("Invalid type for PDB filename %r" % filename)
                
        sel = set()
        
        # Check that the PDB file exists.
        filename = PLATFORM.get_path(filename)
        if os.path.exists(filename):

            # Try to open it as a PDB file. Otherwise throw an error.
            try:
                pdbConf = PDBConfiguration(filename)
            except:
                pass
            else:
                # Will contain the PDB positions of the atoms marked for selection. 
                pdbSelection = []
    
                # Loop over the atoms of the PDB file to get the atoms whose occupancy is set to 1.00.
                for res in pdbConf.residues:
                    for at in res:
                        if at.properties['occupancy'] == 1.0:
                            pdbSelection.append(tuple([at.position]))

                # A dictionnary whose key,value are respectively the position of the atoms of the universe and their index.
                univCoord = {}
                for at in self._universe.atomList():
                    univCoord[tuple([round(v, 4) for v in at.position()])] = at

                # Loop over the PDB atoms marked for selection.
                for p in pdbSelection:
                    # Add to the selection the index of the atom that matches this position.
                    if univCoord.has_key(p):
                        sel.update([univCoord[p]])
                        
        return sel
    
REGISTRY["pdf_file"] = PDBFile
