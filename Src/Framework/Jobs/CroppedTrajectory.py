# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/CroppedTrajectory.py
# @brief     Implements module/class/test CroppedTrajectory
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MMTK.Collections import Collection
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

class CroppedTrajectory(IJob):
    """
    Crop a trajectory in terms of the contents of the simulation box (selected atoms or molecules) and the trajectory length.
    """
        
    label = "Cropped Trajectory"

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
                
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].universe)
        
        # The collection of atoms corresponding to the atoms selected for output.
        indexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]        
        self._selectedAtoms = Collection([atoms[ind] for ind in indexes])

        # The output trajectory is opened for writing.
        self._ct = Trajectory(self._selectedAtoms, self.configuration['output_files']['files'][0], "w")
        
        # The title for the trajectory is set. 
        self._ct.title = self.__class__.__name__

        # Create the snapshot generator.
        self.snapshot = SnapshotGenerator(self.configuration['trajectory']['instance'].universe, actions = [TrajectoryOutput(self._ct, "all", 0, None, 1)])
                
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
                                        
        # The times corresponding to the running index.
        t = self.configuration['frames']['time'][index]
        
        # A snapshot of the universe is written to the output trajectory.
        self.snapshot(data = {'time': t})
                                
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
        self._ct.close()   

REGISTRY['ct'] = CroppedTrajectory
