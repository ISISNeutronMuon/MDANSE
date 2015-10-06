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
import itertools

import numpy

from MDANSE.Core.Error import Error 
from MDANSE.Extensions import distance_histogram
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import atomindex_to_moleculeindex

class DistanceHistogram(IJob):
    """
    Compute the Histogram of Distance, used by e.g. PDF, coordination number analysis
    """
    
    type = None
    
    settings = collections.OrderedDict()    
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['r_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']

        self._indexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]        
        self._indexes = numpy.array(self._indexes,dtype=numpy.int32)
        
        self.selectedElements = self.configuration['atom_selection']['unique_names']
                
        self.indexToSymbol = numpy.array([self.selectedElements.index(name) for name in self.configuration['atom_selection']['names']], dtype = numpy.int32)
                        
        lut = atomindex_to_moleculeindex(self.configuration['trajectory']['instance'].universe)
                        
        self.indexToMolecule = numpy.array([lut[i] for i in self._indexes], dtype=numpy.int32)
        
        nElements = len(self.selectedElements)
        
        # The histogram of the intramolecular distances.
        self.hIntra = numpy.zeros((nElements,nElements,len(self.configuration['r_values']['mid_points'])),dtype=numpy.float64)
        
        # The histogram of the intermolecular distances.
        self.hInter = numpy.zeros((nElements,nElements,len(self.configuration['r_values']['mid_points'])),dtype=numpy.float64)
        
        self.scaleconfig = numpy.zeros((self.configuration['atom_selection']['selection_length'],3), dtype=numpy.float64)

        self.averageDensity = 0.0
        
        self._nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        self._concentrations = {}
        for k in self._nAtomsPerElement.keys():
            self._concentrations[k] = 0.0
        
        self._elementsPairs = sorted(itertools.combinations_with_replacement(self.selectedElements,2))

        if not self.configuration['trajectory']['instance'].universe.is_periodic:
            raise Error("Pair distribution function cannot be calculated for infinite universe trajectories")
 
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. cellVolume (float): the volume of the current frame simulation box
            #. hIntraTemp (np.array): The calculated distance intra-molecular histogram
            #. hInterTemp (np.array): The calculated distance inter-molecular histogram
        """


        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]   

        universe = self.configuration['trajectory']['instance'].universe
        
        universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
    
        directCell = numpy.array(universe.basisVectors()).astype(numpy.float64)
        reverseCell = numpy.array(universe.reciprocalBasisVectors()).astype(numpy.float64)
        
        cellVolume = universe.cellVolume()
            
        hIntraTemp = numpy.zeros(self.hIntra.shape, dtype=numpy.float64)
        hInterTemp = numpy.zeros(self.hInter.shape, dtype=numpy.float64)
        
        distance_histogram.distance_histogram(universe.configuration().array[self._indexes,:],
                                              directCell,
                                              reverseCell,
                                              self._indexes,
                                              self.indexToMolecule,
                                              self.indexToSymbol,
                                              hIntraTemp,
                                              hInterTemp,
                                              self.scaleconfig,
                                              self.configuration['r_values']['first'],
                                              self.configuration['r_values']['step'])

        numpy.multiply(hIntraTemp, cellVolume, hIntraTemp)
        numpy.multiply(hInterTemp, cellVolume, hInterTemp)
                                                                                                
        return index, (cellVolume, hIntraTemp, hInterTemp)
                    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        
        nAtoms = self.configuration['trajectory']['instance'].universe.numberOfAtoms()
        
        self.averageDensity += nAtoms/x[0]

        # The temporary distance histograms are normalized by the volume. This is done for each step because the
        # volume can variate during the MD (e.g. NPT conditions). This volume is the one that intervene in the density
        # calculation.
        self.hIntra += x[1]
        self.hInter += x[2]
        
        for k,v in self._nAtomsPerElement.items():
            self._concentrations[k] += float(v)/nAtoms
                