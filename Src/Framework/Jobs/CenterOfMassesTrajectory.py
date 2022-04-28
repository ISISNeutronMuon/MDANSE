# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/CenterOfMassesTrajectory.py
# @brief     Implements module/class/test CenterOfMassesTrajectory
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import copy

from MMTK import Atom
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import partition_universe

class CenterOfMassesTrajectory(IJob):
    """
    Creates a trajectory from the centre of masses for selected groups of atoms in a given input trajectory.
	For a molecular system, the centre of mass trajectory will contain only the molecular translations, which are therefore separated from the rotations.
    """
        
    label = "Center Of Masses Trajectory"

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}, 'default':(0,1,1)})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
                                        
        self._partition = partition_universe(self.configuration['trajectory']['instance'].universe,self.configuration['atom_selection']['indexes'])

        self._newUniverse = copy.copy(self.configuration['trajectory']['instance'].universe)
        
        self._newUniverse.removeObject(self._newUniverse.objectList()[:])
        
        for i,g in enumerate(self._partition):
            at = Atom("H", name="com_%d" % i)
            at._mass = g.mass()
            at.index = i
            self._newUniverse.addObject(at)    
                            
        # The output trajectory is opened for writing.
        self._comt = Trajectory(self._newUniverse, self.configuration['output_files']['files'][0], "w")
        
        # The title for the trajectory is set. 
        self._comt.title = self.__class__.__name__
        
        # Create the snapshot generator.
        self._snapshot = SnapshotGenerator(self._newUniverse, actions = [TrajectoryOutput(self._comt, ("configuration","time"), 0, None, 1)])

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
              
        # The configuration corresponding to this index is set to the universe.
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        
        comConf = self._newUniverse.configuration().array

        for i, atoms in enumerate(self._partition):
            comConf[i,:] = atoms.centerOfMass()
            
        # The times corresponding to the running index.
        t = self.configuration['frames']['time'][index]
        
        self._newUniverse.foldCoordinatesIntoBox()
        
        # A snapshot of the universe is written to the output trajectory.
        self._snapshot(data={'time': t})
                                
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
        self._comt.close()   

REGISTRY['comt'] = CenterOfMassesTrajectory
