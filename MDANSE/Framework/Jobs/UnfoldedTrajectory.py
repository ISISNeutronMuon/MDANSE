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

@author: Bachir Aoun, Eric C. Pellegrini
'''

import collections
import sys

import numpy

from MMTK import Atom
from MMTK.ChemicalObjects import isChemicalObject
from MMTK.Collections import Collection
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

def contiguous_configuration(seed,atoms,boxCoords):

    atoms.remove(seed)
    
    for bAt in seed.bondedTo():        
        if bAt in atoms:
            diff = boxCoords[bAt.index,:] - boxCoords[seed.index,:]
            boxCoords[bAt.index,:] = numpy.where(numpy.abs(diff)>0.5,boxCoords[bAt.index,:]-numpy.round(diff),boxCoords[bAt.index,:])
            contiguous_configuration(bAt,atoms,boxCoords)

class UnfoldedTrajectory(IJob):
    """
	Tries to make a contiguous trajectory for a whole molecule e.g. a protein.
	The routine may fail if the molecule is bigger than half of the box side (L/2)
    and or the initial structure is not in itself contiguous.	
    """
    
    type = 'ut'
    
    label = "Unfolded Trajectory"

    category = ('Trajectory',)
    
    ancestor = "mmtk_trajectory"
        
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
        
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
         
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].universe)
         
        # The collection of atoms corresponding to the atoms selected for output.
        self._selectedAtoms = Collection([atoms[ind] for ind in self.configuration['atom_selection']['indexes']])
        
        self._chemicalObjects = set([at.topLevelChemicalObject() for at in self._selectedAtoms])
                                         
        # The output trajectory is opened for writing.
        self._outputTraj = Trajectory(self._selectedAtoms, self.configuration['output_files']['files'][0], "w")
         
        # The title for the trajectory is set. 
        self._outputTraj.title = self.__class__.__name__
 
        # Create the snapshot generator.
        self.snapshot = SnapshotGenerator(self.configuration['trajectory']['instance'].universe, actions = [TrajectoryOutput(self._outputTraj, "all", 0, None, 1)])
                 
        # This will store the configuration used as the reference for the following step. 
        self._refCoords = None
        
        # Increase the recursion limit to avoid maximum recursion depth error when calling the contiguous_object recursive function 
        self._oldRecursionLimit = sys.getrecursionlimit()
        sys.setrecursionlimit(100000)

    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. None
        """

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]
        
        universe = self.configuration['trajectory']['instance'].universe 
      
        # The configuration corresponding to this index is set to the universe.
        universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
                
        # Case of the first frame.
        if self._refCoords is None:
                        
            self._refCoords = universe._realToBoxPointArray(universe.configuration().array)

            for obj in universe.objectList():
                                            
                if not isChemicalObject(obj):
                    continue
            
                if isinstance(obj,Atom):
                    continue
                
                if not obj in self._chemicalObjects:
                    continue
                
                atoms = obj.atomList()[:]
                contiguous_configuration(atoms[0],atoms,self._refCoords)
                                                                    
        # Case of the other frames.
        else:
                                
            currentCoords = universe._realToBoxPointArray(universe.configuration().array)
        
            diff = currentCoords - self._refCoords
        
            self._refCoords = numpy.where(numpy.abs(diff)>0.5,currentCoords-numpy.round(diff),currentCoords)
        
        corrCoords = universe._boxToRealPointArray(self._refCoords)
        
        universe.configuration().array = corrCoords
                                 
        # The times corresponding to the running index.
        t = self.configuration['frames']['time'][index]
        
        # Write the step.
        self.snapshot(data = {'time' : t})
                                                                                
        return index, None
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """  
        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """     
        # The input trajectory is closed.
        self.configuration['trajectory']['instance'].close()
                                 
        # The output trajectory is closed.
        self._outputTraj.close()
        
        sys.setrecursionlimit(self._oldRecursionLimit)                