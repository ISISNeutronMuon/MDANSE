# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/RigidBodyTrajectory.py
# @brief     Implements module/class/test RigidBodyTrajectory
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np

import h5py

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import AtomCluster
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Mathematics.LinearAlgebra import Quaternion, Vector
from MDANSE.Mathematics.Transformation import Translation
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.MolecularDynamics.Trajectory import RigidBodyTrajectory, TrajectoryWriter, sorted_atoms

class RigidBodyTrajectory(IJob):
    """
    """
    
    label = 'Rigid Body Trajectory'

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory']=('hdf_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"default" : "atom","dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['reference']=('integer',{"mini":0})
    settings['remove_translation']=('boolean',{'default':False})
    settings['output_files']=('output_files', {"formats":["netcdf"]})
    
    def initialize(self):
        """
        """
        
        self.numberOfSteps = self.configuration['frames']['number']
         
        if (self.configuration['reference']['value'] >= self.configuration['trajectory']['length']):
            raise JobError(self,'Invalid reference frame. Must be an integer in [%d,%d[' % (0,self.configuration['trajectory']['length']))
                           
        self._quaternions = np.zeros((self.configuration['atom_selection']['selection_length'],self.configuration['frames']['number'], 4),dtype=np.float64)
        self._coms = np.zeros((self.configuration['atom_selection']['selection_length'],self.configuration['frames']['number'], 3),dtype=np.float64)
        self._fits = np.zeros((self.configuration['atom_selection']['selection_length'],self.configuration['frames']['number']),dtype=np.float64)
            
        atoms = sorted_atoms(self.configuration['trajectory'].chemical_system.atom_list())

        self._groups = []

        for i in range(self.configuration['atom_selection']['selection_length']):
            indexes = self.configuration['atom_selection']["indexes"][i]
            self._groups.append(AtomCluster('',[atoms[idx] for idx in indexes]))

        self.referenceFrame = self.configuration['reference']['value']

        trajectory = self.configuration['trajectory']['instance']

        coords = trajectory.coordinates(self.referenceFrame)
        unitCell = trajectory.unit_cell(self.referenceFrame)
        
        conf = RealConfiguration(trajectory.chemical_system,coords,unitCell)

        self._reference_configuration = conf.continuous_configuration()

        selectedAtoms = []        
        for indexes in self.configuration['atom_selection']['indexes']:
            for idx in indexes:
                selectedAtoms.append(atoms[idx])

        # Create trajectory
        self._output_trajectory = TrajectoryWriter(self.configuration['output_files']['files'][0], trajectory.chemical_system, selectedAtoms)
    
    def run_step(self, index):
        """
        """

        trajectory = self.configuration['trajectory']['instance']
                                    
        currentFrame = self.configuration['frames']['value'][index]

        real_configuration = trajectory.configuration(currentFrame)

        for group_id, group in enumerate(self._groups):
            
            rbt = RigidBodyTrajectory(
                trajectory,
                group,
                first = currentFrame,
                last = currentFrame+1,
                step = 1,
                reference = self._reference_configuration)

            center_of_mass = group.center_of_mass(self._reference_configuration)
                             
            # The rotation matrix corresponding to the selected frame in the RBT.
            transfo = Quaternion(rbt.quaternions[0]).asRotation()

            if self.configuration['remove_translation']['value']:
                # The transformation matrix corresponding to the selected frame in the RBT.
                transfo = Translation(center_of_mass)*transfo
                               
            # Compose with the CMS translation if the removeTranslation flag is set off.
            else:
                # The transformation matrix corresponding to the selected frame in the RBT.
                transfo = Translation(Vector(self._coms[group_id,index,:]))*transfo

            # Loop over the atoms of the group to set the RBT trajectory.
            for atom in group.atom_list():
                                                      
                # The coordinates of the atoms are centered around the center of mass of the group.
                xyz = self.referenceConfiguration[atom] - center_of_mass

                real_configuration['coordinates'][atom.index,:] = transfo(Vector(xyz))
                                                                             
            self._quaternions[group_id,index,:] = rbt.quaternions[0]
            self._coms[group_id,index,:] = rbt.cms[0]
            self._fits[group_id,index] = rbt.fit[0]

        self._output_trajectory._chemical_system.configuration = real_configuration

        self._output_trajectory.dump_configuration(self.configuration['frames']['time'][currentFrame])
        
        return index, None

    def combine(self, index, x):
        """
        """
        
        pass
                
    def finalize(self):
        '''
        '''
        
        outputFile = h5py.File(self.configuration['output_files']['files'][0], 'r+')
 
        n_groups = self.configuration['atom_selection']['selection_length']
        n_frames = self.configuration['frames']['number']

        quaternions = outputFile.create_dataset('quaternions',shape=(n_groups, n_frames, 4),dtype=np.float)

        coms = outputFile.create_dataset('coms',shape=(n_groups, n_frames, 3),dtype=np.float)
              
        fits = outputFile.create_dataset('fits',shape=(n_groups, n_frames),dtype=np.float)
  
        outputFile.attrs['info'] = str(self)
   
        # Loop over the groups.
        for comp in range(self.configuration['atom_selection']['selection_length']):
               
            aIndexes = self.configuration['atom_selection']['indexes'][comp]
               
            outputFile.attrs['info'] += 'Group %s: %s\n' % (comp, [index for index in aIndexes])

            quaternions[comp,:,:] = self._quaternions[comp,:,:]
            coms[comp,:,:] = self._coms[comp,:,:]
            fits[comp,:] = self._fits[comp,:]
                           
        outputFile.close()
        
REGISTRY['rbt'] = RigidBodyTrajectory
