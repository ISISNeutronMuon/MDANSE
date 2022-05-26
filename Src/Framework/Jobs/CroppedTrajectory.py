# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/CroppedTrajectory.py
# @brief     Implements module/class/test CroppedTrajectory
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import AtomGroup
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

class CroppedTrajectory(IJob):
    """
    Crop a trajectory in terms of the contents of the simulation box (selected atoms or molecules) and the trajectory length.
    """
        
    label = "Cropped Trajectory"

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('hdf_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    settings['output_files'] = ('output_files', {'formats':["hdf"]})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
                
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].chemical_system.atom_list())
        
        # The collection of atoms corresponding to the atoms selected for output.
        indexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]        
        self._selectedAtoms = [atoms[ind] for ind in indexes]

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration['output_files']['files'][0],
            self.configuration['trajectory']['instance'].chemical_system,
            self.numberOfSteps,
            self._selectedAtoms)
                        
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
        frame_index = self.configuration['frames']['value'][index]
              
        conf = self.configuration['trajectory']['instance'].configuration(frame_index)

        cloned_conf = conf.clone(self._output_trajectory.chemical_system)

        self._output_trajectory.chemical_system.configuration = cloned_conf

        time = self.configuration['frames']['time'][index]

        self._output_trajectory.dump_configuration(time)

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
        self._output_trajectory.close()   

REGISTRY['ct'] = CroppedTrajectory
