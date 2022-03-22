# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/RigidBodyTrajectory.py
# @brief     Implements module/class/test RigidBodyTrajectory
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import operator

import numpy

from Scientific.Geometry import Vector
from Scientific.Geometry.Quaternion import Quaternion
from Scientific.Geometry.Transformation import Translation
from Scientific.IO.NetCDF import NetCDFFile

from MMTK.Collections import Collection
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob, JobError

class RigidBodyTrajectory(IJob):
    """
    """
    
    label = 'Rigid Body Trajectory'

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory']=('mmtk_trajectory',{})
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
                           
        self._quaternions = numpy.zeros((self.configuration['atom_selection']['selection_length'],self.configuration['frames']['number'], 4),dtype=numpy.float64)
        self._coms = numpy.zeros((self.configuration['atom_selection']['selection_length'],self.configuration['frames']['number'], 3),dtype=numpy.float64)
        self._fits = numpy.zeros((self.configuration['atom_selection']['selection_length'],self.configuration['frames']['number']),dtype=numpy.float64)
            
        atoms = sorted(self.configuration['trajectory']['universe'].atomList(), key=operator.attrgetter('index'))

        self._groups = []

        for i in range(self.configuration['atom_selection']['selection_length']):
            indexes = self.configuration['atom_selection']["indexes"][i]
            self._groups.append(Collection([atoms[idx] for idx in indexes]))

        self.referenceFrame = self.configuration['reference']['value']

        trajectory = self.configuration['trajectory']['instance'] 
        self.referenceConfiguration = trajectory.universe.contiguousObjectConfiguration(conf = trajectory.configuration[self.referenceFrame])

        selectedAtoms = Collection()
        for indexes in self.configuration['atom_selection']['indexes']:
            for idx in indexes:
                selectedAtoms.addObject(atoms[idx])

        # Create trajectory
        self.outputFile = Trajectory(selectedAtoms, self.configuration['output_files']['files'][0], 'w')
        
        # Create the snapshot generator
        self.snapshot = SnapshotGenerator(self.configuration['trajectory']['universe'], actions = [TrajectoryOutput(self.outputFile, ["configuration","time"], 0, None, 1)])

    
    def run_step(self, index):
        '''
        '''

        trajectory = self.configuration['trajectory']['instance']
                                    
        currentFrame = self.configuration['frames']['value'][index]
                
        for group_id, group in enumerate(self._groups):
            
            rbt = trajectory.readRigidBodyTrajectory(group,
                                                     first = currentFrame,
                                                     last = currentFrame+1,
                                                     skip = 1,
                                                     reference = self.referenceConfiguration)

            centerOfMass = group.centerOfMass(self.referenceConfiguration)
                             
            # The rotation matrix corresponding to the selected frame in the RBT.
            transfo = Quaternion(rbt.quaternions[0]).asRotation()


            if self.configuration['remove_translation']['value']:
                # The transformation matrix corresponding to the selected frame in the RBT.
                transfo = Translation(centerOfMass)*transfo
                               
            # Compose with the CMS translation if the removeTranslation flag is set off.
            else:
                # The transformation matrix corresponding to the selected frame in the RBT.
                transfo = Translation(Vector(self._coms[group_id,index,:]))*transfo

                             
            # Loop over the atoms of the group to set the RBT trajectory.
            for atom in group:
                                                      
                # The coordinates of the atoms are centered around the center of mass of the group.
                xyz = self.referenceConfiguration[atom] - centerOfMass
                                                                                          
                atom.setPosition(transfo(Vector(xyz)))
                
            self._quaternions[group_id,index,:] = rbt.quaternions[0]
            self._coms[group_id,index,:] = rbt.cms[0]
            self._fits[group_id,index] = rbt.fit[0]
         
        self.snapshot(data = {'time' : self.configuration['frames']['time'][currentFrame]})
        
        return index, None

    def combine(self, index, x):
        """
        """
        
        pass
                
    def finalize(self):
        '''
        '''
        
        outputFile = NetCDFFile(self.configuration['output_files']['files'][0], 'a')
 
        outputFile.createDimension('NGROUPS', self.configuration['atom_selection']['selection_length'])
        outputFile.createDimension('NFRAMES', self.configuration['frames']['number'])
        outputFile.createDimension('QUATERNIONLENGTH',4)
        outputFile.createDimension('XYZ',3)

        # The NetCDF variable that stores the quaternions.
        QUATERNIONS = outputFile.createVariable('quaternions', numpy.dtype(numpy.float64).char, ('NGROUPS','NFRAMES','QUATERNIONLENGTH'))
  
        # The NetCDF variable that stores the centers of mass.
        COM = outputFile.createVariable('coms', numpy.dtype(numpy.float64).char, ('NGROUPS','NFRAMES','XYZ'))
              
        # The NetCDF variable that stores the rigid-body fit.
        FIT = outputFile.createVariable('fits', numpy.dtype(numpy.float64).char, ('NGROUPS','NFRAMES'))
  
        outputFile.info = str(self)
   
        # Loop over the groups.
        for comp in range(self.configuration['atom_selection']['selection_length']):
               
            aIndexes = self.configuration['atom_selection']['indexes'][comp]
               
            outputFile.info += 'Group %s: %s\n' % (comp, [index for index in aIndexes])

        QUATERNIONS.assignValue(self._quaternions[comp,:,:])
        COM.assignValue(self._coms[comp,:,:])
        FIT.assignValue(self._fits[comp,:])
                           
        outputFile.close()
        
REGISTRY['rbt'] = RigidBodyTrajectory
