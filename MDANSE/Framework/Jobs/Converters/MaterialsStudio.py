#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#71 avenue des Martyrs
#38000 Grenoble Cedex 9
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
Created on Apr 10, 2015

:author: Eric C. Pellegrini
'''

import collections
import xml.etree.ElementTree as ElementTree

import numpy

from MMTK import Units
from MMTK import Atom, AtomCluster
from MMTK.ParticleProperties import Configuration
from MMTK.Universe import InfiniteUniverse, ParallelepipedicPeriodicUniverse

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
                

    def _build_universe(self, idx, clustered, cluster):
        """
        """

        clustered[idx] = True
        cluster.append(idx)
        
        at = self._atoms[idx]
        
        for nidx in at["bonded_to"]:
            
            if nidx in clustered:
                continue
            
            self._build_universe(nidx, clustered, cluster)
            

    def build_universe(self):        

        if self._pbc:
            self._universe = ParallelepipedicPeriodicUniverse()
            self._universe.setShape(self._cell)
        else:
            self._universe = InfiniteUniverse()
            
        clustered = {}
        
        cluster = []
        
        configuration = numpy.empty((self._nAtoms,3),dtype=numpy.float64)
                            
        for idx in self._atoms.keys():
            
            if idx in clustered:
                continue

            self._build_universe(idx, clustered, cluster)

            clustername = collections.defaultdict(lambda : 0)
            
            ac = []
            for idx in cluster:
                element = self._atoms[idx]["element"]
                name = self._atoms[idx]["name"]
                at = Atom(element, name=name, xtdIndex=idx)
                at.index = self._atoms[idx]["mmtk_index"]
                configuration[at.index] = self._atoms[idx]["xyz"]
                ac.append(at)
                clustername[element] += 1
            clustername = "".join(["%s%d" % (k,v) for k,v in sorted(clustername.items())])
            cluster = []
            
            ac = AtomCluster(ac,name=clustername)
            self._universe.addObject(ac)


        if self._pbc:
            configuration = self._universe._boxToRealPointArray(configuration)
        else:
            configuration *= Units.Ang
            
        self._universe.setConfiguration(Configuration(self._universe,configuration))
        self._universe.foldCoordinatesIntoBox()
