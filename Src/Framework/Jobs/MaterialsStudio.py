# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/MaterialsStudio.py
# @brief     Implements module/class/test MaterialsStudio
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import xml.etree.ElementTree as ElementTree

import numpy

from MMTK import Units
from MMTK import Atom, AtomCluster
from MMTK.ParticleProperties import Configuration
from MMTK.Universe import InfiniteUniverse, ParallelepipedicPeriodicUniverse

from MDANSE.Mathematics.Graph import Graph

class XTDFile(object):
    
    def __init__(self, filename):
        
        self._filename = filename
        
        self._atoms = None
        
        self._universe = None
        
        self._pbc = False
        
        self._cell = None
        
        self.parse()
        

    @property
    def clusters(self):
        return self._clusters
    
    
    @property
    def universe(self):
        return self._universe
        
        
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
            self._cell = numpy.empty((3,3),dtype=numpy.float64)
            self._cell[0,:] = SPACEGROUP.attrib["AVector"].split(',')
            self._cell[1,:] = SPACEGROUP.attrib["BVector"].split(',')
            self._cell[2,:] = SPACEGROUP.attrib["CVector"].split(',')
            self._cell *= Units.Ang

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
                info["xyz"] = numpy.array(node.attrib["XYZ"].split(','),dtype=numpy.float64)
    
                name = node.attrib.get('Name','').strip()
                if name:
                    info['atom_name'] = name
                else:                
                    name = node.attrib.get('ForcefieldType','').strip()
                    if name:
                        info['atom_name'] = name + '_ff'
                    else:
                        info['atom_name'] = info['element'] + '_el'
                    
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

    def build_universe(self):        

        if self._pbc:
            self._universe = ParallelepipedicPeriodicUniverse()
            self._universe.setShape(self._cell)
        else:
            self._universe = InfiniteUniverse()
                    
        configuration = numpy.empty((self._nAtoms,3),dtype=numpy.float64)
                                     
        graph = Graph()

        for idx, at in self._atoms.items():
            graph.add_node(name=idx,**at)

        for idx, at in self._atoms.items():
            for bat in at['bonded_to']:
                graph.add_link(idx,bat)

        clusters = graph.build_connected_components()

        prev = 0 
        for cluster in clusters:

            atomCluster = AtomCluster([])

            bruteFormula = collections.defaultdict(lambda : 0)
            
            for node in cluster:
                element = node.element
                name = node.atom_name
                at = Atom(element, name=name, xtdIndex=node.xtd_index)
                at.index = node.mmtk_index
                configuration[at.index] = node.xyz
                atomCluster.atoms.append(at)
                bruteFormula[element] += 1
            atomCluster.name = "".join(["%s%d" % (k,v) for k,v in sorted(bruteFormula.items())])
            self._universe.addObject(atomCluster)

        if self._pbc:
            configuration = self._universe._boxToRealPointArray(configuration)
        else:
            configuration *= Units.Ang
            
        self._universe.setConfiguration(Configuration(self._universe,configuration))
        self._universe.foldCoordinatesIntoBox()
