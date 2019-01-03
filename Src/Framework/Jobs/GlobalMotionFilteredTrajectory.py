# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/GlobalMotionFilteredTrajectory.py
# @brief     Implements module/class/test GlobalMotionFilteredTrajectory
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MMTK.Collections import Collection
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

class GlobalMotionFilteredTrajectory(IJob):
    """
    It is often of interest to separate global translation and rotation motion from internal motion, both for quantitative analysis 
    and for visualization by animated display. Obviously, this can only be done under the hypothesis that global and internal motions 
    are decoupled within the length and timescales of the analysis. MDANSE creates a Global Motion Filtered Trajectory (GMFT) by 
    filtering out global motions (made of the three translational and three rotational degrees of freedom), either on the whole system 
    or on an user-defined subset, by fitting it to a reference structure (usually the first frame of the MD). Global motion filtering 
    uses a straightforward algorithm:
    
    #. for the first frame, find the linear transformation such that the coordinate origin becomes the centre of mass of the system 
    and its principal axes of inertia are parallel to the three coordinates axes (also called principal axes transformation),    
    #. this provides a reference configuration *r*    
    #. for any other frames *f*, find and apply the linear transformation that minimizes the RMS 'distance' between frame *f* and *r*.
    
    The result is stored in a new trajectory file that contains only internal motions. This analysis can be useful in case where 
    overall diffusive motions are not of interest e.g. for a protein in solution and the internal protein dynamics fall within the 
    dynamical range of the instrument.

    In the global motion filtered trajectory, the universe is made infinite and all the configurations contiguous.
    """
        
    label = "Global Motion Filtered Trajectory"

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
        
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['reference_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['contiguous'] = ('boolean', {'default':False, 'label':"Make the chemical object contiguous"})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
        
        # Store universe name for further restoration
        self.old_universe_name = self.configuration['trajectory']['instance'].universe.__class__.__name__

        self.configuration['trajectory']['instance'].universe.__class__.__name__ = 'InfiniteUniverse'
        
        self.configuration['trajectory']['instance'].universe._descriptionArguments = lambda: '()'

        self.configuration['trajectory']['instance'].universe.is_periodic=False        
        
        self._cellParametersFunction = self.configuration['trajectory']['instance'].universe.cellParameters
        

        # The collection of atoms corresponding to the atoms selected for output.
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].universe)
        sIndexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]
        self._selectedAtoms = Collection([atoms[ind] for ind in sIndexes])

        rIndexes  = [idx for idxs in self.configuration['reference_selection']['indexes'] for idx in idxs]
        self._referenceAtoms = Collection([atoms[ind] for ind in rIndexes])
                        
        # The output trajectory is opened for writing.
        self._gmft = Trajectory(self._selectedAtoms, self.configuration['output_files']['files'][0], "w")
        
        # The title for the trajectory is set. 
        self._gmft.title = self.__class__.__name__

        # Create the snapshot generator.
        self.snapshot = SnapshotGenerator(self.configuration['trajectory']['instance'].universe, actions = [TrajectoryOutput(self._gmft, "all", 0, None, 1)])
                
        # This will store the configuration used as the reference for the following step. 
        self._referenceConfig = None

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
        
        if self.configuration['contiguous']["value"]:
            # The configuration is made contiguous.
            conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()        
            # And set to the universe.
            self.configuration['trajectory']['instance'].universe.setConfiguration(conf)
        
        # Case of the first frame.
        if frameIndex == self.configuration['frames']['first']:

            # A a linear transformation that shifts the center of mass of the reference atoms to the coordinate origin 
            # and makes its principal axes of inertia parallel to the three coordinate axes is computed.
            tr = self._referenceAtoms.normalizingTransformation()

            # The first rms is set to zero by construction.
            rms = 0.0
                    
        # Case of the other frames.
        else:
            
            # The linear transformation that minimizes the RMS distance between the current configuration and the previous 
            # one is applied to the reference atoms.
            tr, rms = self._referenceAtoms.findTransformation(self._referenceConfig)
                 
        # And applied to the selected atoms for output.
        self.configuration['trajectory']['instance'].universe.applyTransformation(tr)        

        # The current configuration becomes now the reference configuration for the next step.
        self._referenceConfig = self.configuration['trajectory']['instance'].universe.copyConfiguration()
        
        velocities = self.configuration['trajectory']['instance'].universe.velocities()
        
        if velocities is not None:                    
            rot = tr.rotation()
            for atom in self._selectedAtoms:
                velocities[atom] = rot(velocities[atom])
            self.configuration['trajectory']['instance'].universe.setVelocities(velocities)
                
        # A MMTK.InfiniteUniverse.cellParameters is set to None.
        self.configuration['trajectory']['instance'].universe.cellParameters = lambda: None

        # The times corresponding to the running index.
        t = self.configuration['frames']['time'][index]
        
        # Write the step.
        self.snapshot(data = {'time' : t, 'rms' : rms})
        
        # A MMTK.PeriodicUniverse.cellParameters is et back to the universe.
        self.configuration['trajectory']['instance'].universe.cellParameters = self._cellParametersFunction
                                                                        
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
        self._gmft.close()
        
        # Restore universe name
        self.configuration['trajectory']['instance'].universe.__class__.__name__ = self.old_universe_name
        
REGISTRY['gmft'] = GlobalMotionFilteredTrajectory
