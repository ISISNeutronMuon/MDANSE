# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/MaterialsStudio.py
# @brief     Implements module/class/test MaterialsStudio
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import xml.etree.ElementTree as ElementTree
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration, RealConfiguration

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration, RealConfiguration

class XTDFile(object):
    
    def __init__(self, filename):
        
        self._filename = filename
        
        self._atoms = None
        
        self._chemicalSystem = None
        
        self._pbc = False
        
        self._cell = None
        
        self.parse()

    @property
    def clusters(self):
        return self._clusters
    
    @property
    def chemicalSystem(self):
        return self._chemicalSystem
            
    @property
    def pbc(self):
        return self._pbc
    
    @property
    def cell(self):
        return self._cell
        
    def parse(self):
        """
        Parse the xtd file that is basically xml files with nodes that contains informations about the 
        topology of the molecular system.
        """

        self._file = ElementTree.parse(self._filename)

        ROOT = self._file.getroot()

        SPACEGROUP = list(ROOT.iter("SpaceGroup"))
        
        if SPACEGROUP:
            self._pbc = True
            SPACEGROUP = SPACEGROUP[0]
            self._cell = np.empty((3,3),dtype=np.float64)
            self._cell[0,:] = SPACEGROUP.attrib["AVector"].split(',')
            self._cell[1,:] = SPACEGROUP.attrib["BVector"].split(',')
            self._cell[2,:] = SPACEGROUP.attrib["CVector"].split(',')
            self._cell *= measure(1.0,'ang').toval('nm')

        self._atoms = collections.OrderedDict()
        
        atomsMapping = {}
        
        comp = 0
        for node in ROOT.iter("Atom3d"):

            idx = int(node.attrib['ID'])

            imageOf = node.attrib.get("ImageOf",None)
            
            if imageOf is None:
                
                atomsMapping[idx] = idx
    
                info = {}
                info["mmtk_index"] = comp
                info["xtd_index"] = idx
                info["bonded_to"] = set()
                info["element"] = node.attrib['Components'].split(',')[0].strip()
                info["xyz"] = np.array(node.attrib["XYZ"].split(','),dtype=np.float64)
    
                name = node.attrib.get('Name','').strip()
                if name:
                    info['name'] = name
                else:                
                    name = node.attrib.get('ForcefieldType','').strip()
                    if name:
                        info['name'] = name + '_ff'
                    else:
                        info['name'] = info['element'] + '_el'
                    
                self._atoms[idx] = info
                
                comp += 1
                
            else:
                atomsMapping[idx] = int(imageOf)

        self._nAtoms = len(self._atoms)

        bondsMapping = {}
                
        comp = 0
        for node in ROOT.iter("Bond"):
            
            idx = int(node.attrib['ID'])
            
            imageOf = node.attrib.get("ImageOf",None)

            if imageOf is None:
                bondsMapping[idx] = [atomsMapping[int(v)] for v in node.attrib['Connects'].split(',')]
                idx1,idx2 = bondsMapping[idx]
                self._atoms[idx1]["bonded_to"].add(idx2)
                self._atoms[idx2]["bonded_to"].add(idx1)            

    def build_chemical_system(self):        

        self._chemicalSystem = ChemicalSystem()
                    
        coordinates = np.empty((self._nAtoms,3),dtype=np.float64)
                            
        nclusters = 0
         
        clusters = {}
         
        equivalences = {}
         
        for idx,atom in self._atoms.items():
         
            if not clusters.has_key(idx):
                nclusters += 1
                clusters[idx] = nclusters
             
            for neighbor in atom["bonded_to"]:
                if (neighbor in clusters) and (clusters[idx] != clusters[neighbor]):
                    equivalences[clusters[neighbor]] = equivalences.get(clusters[idx],clusters[idx])
                     
                clusters[neighbor] = clusters[idx]
                         
        mergedClusters = {}
        for idx,clusterId in clusters.items():
            if equivalences.has_key(clusterId):
                mergedClusters.setdefault(equivalences[clusterId],[]).append(idx)
            else:
                mergedClusters.setdefault(clusterId,[]).append(idx)
                 
        for k,indexes in mergedClusters.items():
            bruteFormula = collections.defaultdict(lambda : 0)
            atoms = []
            for idx in indexes:
                element = self._atoms[idx]["element"]
                name = self._atoms[idx]["name"]
                at = Atom(symbol=element, name=name, xtdIndex=idx)
                at.index = self._atoms[idx]["mmtk_index"]
                coordinates[at.index] = self._atoms[idx]["xyz"]
                atoms.append(at)
                bruteFormula[element] += 1
            name = "".join(["%s%d" % (k,v) for k,v in sorted(bruteFormula.items())])
            ac = AtomCluster(name,atoms)
            self._chemicalSystem.add_chemical_entity(ac)

        if self._pbc:
            boxConf = PeriodicBoxConfiguration(self._chemicalSystem,coordinates,self._cell)
            realConf = boxConf.to_real_configuration()
        else:
            coordinates *= measure(1.0,'ang').toval('nm')
            realConf = RealConfiguration(self._chemicalSystem,coordinates,self._cell)

        realConf.fold_coordinates()            
        self._chemicalSystem.configuration = realConf