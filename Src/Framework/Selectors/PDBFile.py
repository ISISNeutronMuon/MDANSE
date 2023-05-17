# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/PDBFile.py
# @brief     Implements module/class/test PDBFile
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
        
        if not isinstance(filename,str):
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
                    if p in univCoord:
                        sel.update([univCoord[p]])
                        
        return sel
    
REGISTRY["pdf_file"] = PDBFile
