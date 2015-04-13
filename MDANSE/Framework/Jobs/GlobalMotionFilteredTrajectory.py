#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
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

@author: pellegrini
'''

import collections

from MMTK.Collections import Collection
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

class GlobalMotionFilteredTrajectory(IJob):
    """
    It is often of interest to separate global motion from internal motion, both for quantitative
    analysis and for visualization by animated display. Obviously, this can be done under the
    hypothesis that global and internal motions are decoupled within the length and timescales of
    the analysis. nMoldyn can create Global Motion Filtered Trajectory (GMFT) by filtering
    out global motions (made of the three translational and rotational degrees of freedom), either
    on the whole system or on an user-defined subset, by fitting it to a reference structure (usually
    the first frame of the MD). Global motion filtering uses a straightforward algorithm:
    
    * for the first frame, find the linear transformation such that the coordinate origin becomes
    the center of mass of the system and its principal axes of inertia are parallel to the three
    coordinates axes (also called principal axes transformation),
    
    * this provides a reference configuration C ref ,
    
    * for any other frames f, finds and applies the linear transformation that minimizes the
    RMS distance between frame f and C ref .
    
    The result is stored in a new trajectory file that contains only internal motions. This analysis
    can be useful in case where diffusive motions are not of interest or simply not accessible to the
    experiment (time resolution, powder analysis ... ).

    To do so, the universe has to be made infinite and all its configuration contiguous.
    """
    
    type = 'gmft'
    
    label = "Global Motion Filtered Trajectory"

    category = ('Trajectory',)
    
    ancestor = "mmtk_trajectory"
        
    configurators = collections.OrderedDict()
    configurators['trajectory'] = ('mmtk_trajectory',{})
    configurators['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    configurators['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    configurators['reference_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    configurators['contiguous'] = ('boolean', {'default':False, 'label':"Make the chemical object contiguous"})
    configurators['output_files'] = ('output_files', {'formats':["netcdf"]})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
                
        self.configuration['trajectory']['instance'].universe.__class__.__name__ = 'InfiniteUniverse'
        
        self.configuration['trajectory']['instance'].universe._descriptionArguments = lambda: '()'

        self.configuration['trajectory']['instance'].universe.is_periodic=False        
        
        self._cellParametersFunction = self.configuration['trajectory']['instance'].universe.cellParameters
        
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].universe)

        # The collection of atoms corresponding to the atoms selected for output.
        self._selectedAtoms = Collection([atoms[ind] for ind in self.configuration['atom_selection']['indexes']])

        self._referenceAtoms = Collection([atoms[ind] for ind in self.configuration['reference_selection']['indexes']])
                        
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