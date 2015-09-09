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
Created on Jun 9, 2015

:author: Erc C. Pellegrini
'''

import collections
import operator

import numpy

from Scientific.Geometry import Vector
from Scientific.Geometry.Quaternion import Quaternion
from Scientific.Geometry.Transformation import Translation
from Scientific.IO.NetCDF import NetCDFFile

from MMTK.Collections import Collection
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE.Framework.Jobs.IJob import IJob, JobError

class RigidBodyTrajectory(IJob):
    """
    """

    type = 'rbt'
    
    label = 'Rigid Body Trajectory'

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory']=('mmtk_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory','grouping_level':'grouping_level'}})
    settings['grouping_level']=('grouping_level',{})
    settings['stepwise']=('boolean',{'default':True})
    settings['reference']=('integer',{"mini":0})
    settings['remove_translation']=('integer',{'default':False})
    settings['output_files']=('output_files', {"formats":["netcdf"]})
    settings['running_mode']=('running_mode',{})
    
    def initialize(self):
        """
        """

        self.numberOfSteps = self.configuration['atom_selection']['n_groups'] 
         
        if (self.configuration['reference']['value'] >= self.configuration['trajectory']['length']):
            raise JobError(self,'Invalid reference frame. Must be an integer in [%d,%d[' % (0,self.configuration['trajectory']['length']))
                           
        self.nFrames = self.configuration['frames']['number']                  
        self._rbt = {'trajectory':{}}
        
        self._quaternions = numpy.zeros((self.configuration['atom_selection']['n_groups'],self.configuration['frames']['number'], 4),dtype=numpy.float64)
        self._coms = numpy.zeros((self.configuration['atom_selection']['n_groups'],self.configuration['frames']['number'], 3),dtype=numpy.float64)
        self._fits = numpy.zeros((self.configuration['atom_selection']['n_groups'],self.configuration['frames']['number']),dtype=numpy.float64)
            
    def run_step(self, index):
        '''
        '''
        
        indexes = self.configuration['atom_selection']['groups'][index]
        
        atoms = sorted(self.configuration['trajectory']['universe'].atomList(), key=operator.attrgetter('index'))
 
        group = Collection([atoms[idx] for idx in indexes])
         
        rbtPerGroup = {}        
        # Those matrix will store the quaternions and the CMS coming from the RBT trajectory.
        rbtPerGroup['quaternions'] = numpy.zeros((self.configuration['frames']['number'], 4), dtype=numpy.float64)
        rbtPerGroup['com'] = numpy.zeros((self.configuration['frames']['number'], 3), dtype=numpy.float64)
        rbtPerGroup['fit'] = numpy.zeros((self.configuration['frames']['number'],), dtype=numpy.float64)
        rbtPerGroup['trajectory'] = {}
         
        # Case of a moving reference.
        if self.configuration['stepwise']['value']:
             
            # The reference configuration is always the one of the previous frame excepted for the first frame
            # where it is set by definition to the first frame (could we think about a cyclic alternative way ?).
            for comp in range(self.configuration['frames']['number']):
                                  
                if comp == 0:
                    previousFrame = self.configuration['frames']['value'][0]
                     
                else:
                    previousFrame = self.configuration['frames']['value'][comp-1]
                    
                currentFrame = self.configuration['frames']['value'][comp]                    
                     
                refConfig = self.configuration['trajectory']['instance'].configuration[previousFrame]
 
                # The RBT is created just for the current step.
                rbt = self.configuration['trajectory']['instance'].readRigidBodyTrajectory(group,
                                                                                           first=currentFrame,
                                                                                           last=currentFrame+1,
                                                                                           skip=1,
                                                                                           reference=refConfig)
 
                # The corresponding quaternions and cms are stored in their corresponding matrix.
                rbtPerGroup['quaternions'][comp,:] = rbt.quaternions
                rbtPerGroup['com'][comp,:] = rbt.cms
                rbtPerGroup['fit'][comp] = rbt.fit
                                             
        # The simplest case, the reference frame is fixed.
        # A unique RBT is performed from first to last skipping skip steps and using refConfig as the reference.
        else:
            
            # If a fixed reference has been set. We can already set the reference configuration here.
            refConfig = self.configuration['trajectory']['instance'].configuration[self.configuration['reference']['value']]
             
            # The RBT is created for the whole frame selection
            rbt = self.configuration['trajectory']['instance'].readRigidBodyTrajectory(group,
                                                                                       first=self.configuration['frames']['first'],
                                                                                       last=self.configuration['frames']['last']+1,
                                                                                       skip=self.configuration['frames']['step'],
                                                                                       reference=refConfig)
             
            # The corresponding quaternions and cms are stored in their corresponding matrix.
            rbtPerGroup['quaternions'] = rbt.quaternions
            rbtPerGroup['com'] = rbt.cms
            rbtPerGroup['fit'] = rbt.fit
 
        # Can not use the centers of mass defined by rbt.cms because the reference frame selected can be out of the selected frames for the Rigid Body Trajectory.
        centerOfMass = group.centerOfMass(refConfig)
 
        # Loop over the atoms of the group to set the RBT trajectory.
        for atom in group:
                         
            rbtPerGroup['trajectory'][atom.index] = numpy.zeros((self.configuration['frames']['number'],3), dtype=numpy.float64)
             
            # The coordinates of the atoms are centered around the center of mass of the group.
            xyz = refConfig[atom] - centerOfMass
 
            # Loop over the selected frames.
            for comp in range(self.configuration['frames']['number']):
                 
                # The rotation matrix corresponding to the selected frame in the RBT.
                transfo = Quaternion(rbtPerGroup['quaternions'][comp,:]).asRotation()
 
                if self.configuration['remove_translation']['value']:
                    # The transformation matrix corresponding to the selected frame in the RBT.
                    transfo = Translation(centerOfMass)*transfo
                         
                # Compose with the CMS translation if the removeTranslation flag is set off.
                else:
                    # The transformation matrix corresponding to the selected frame in the RBT.
                    transfo = Translation(Vector(rbtPerGroup['com'][comp,:]))*transfo
 
                # The RBT is performed on the CMS centered coordinates of atom at.
                rbtPerGroup['trajectory'][atom.index][comp,:] = transfo(Vector(xyz))
                                         
        return index, rbtPerGroup
    
    def combine(self, index, x):
        """
        """
        
        self._quaternions[index] = x['quaternions']
        self._coms[index] = x['com']
        self._fits[index] = x['fit']
        
        self._rbt['trajectory'].update(x['trajectory'])
        
    def finalize(self):
        '''
        '''
        
        selectedAtoms = Collection()
        atoms = sorted(self.configuration['trajectory']['universe'].atomList(), key=operator.attrgetter('index'))
        [[selectedAtoms.addObject(atoms[idx]) for idx in indexes] for indexes in self.configuration['atom_selection']['groups']]

        # Create trajectory
        outputFile = Trajectory(selectedAtoms, self.configuration['output_files']['files'][0], 'w')

        # Create the snapshot generator
        snapshot = SnapshotGenerator(self.configuration['trajectory']['universe'], actions = [TrajectoryOutput(outputFile, ["configuration","time"], 0, None, 1)])
                
        # The output is written
        for comp in range(self.configuration['frames']['number']):

            currentFrame = self.configuration['frames']['value'][comp]                    

            self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], currentFrame)
            
            for atom in selectedAtoms:
                atom.setPosition(self._rbt['trajectory'][atom.index][comp,:])
            snapshot(data = {'time' : self.configuration['frames']['time'][comp]})
  
        outputFile.close()

        outputFile = NetCDFFile(self.configuration['output_files']['files'][0], 'a')

        outputFile.createDimension('NFRAMES', self.configuration['frames']['number'])
        outputFile.createDimension('NGROUPS', self.configuration['atom_selection']['n_groups'])
        outputFile.createDimension('QUATERNIONLENGTH',4)
 
        # The NetCDF variable that stores the quaternions.
        QUATERNIONS = outputFile.createVariable('quaternion', numpy.dtype(numpy.float64).char, ('NGROUPS', 'NFRAMES','QUATERNIONLENGTH'))
 
        # The NetCDF variable that stores the centers of mass.
        COM = outputFile.createVariable('com', numpy.dtype(numpy.float64).char, ('NGROUPS','NFRAMES','xyz'))
             
        # The NetCDF variable that stores the rigid-body fit.
        FIT = outputFile.createVariable('fit', numpy.dtype(numpy.float64).char, ('NGROUPS','NFRAMES'))
 
        outputFile.info = self._info
 
        # Loop over the groups.
        for comp in range(self.configuration['atom_selection']['n_groups']):
             
            aIndexes = self.configuration['atom_selection']['groups'][comp]
             
            outputFile.info += 'Group %s: %s\n' % (comp, [index for index in aIndexes])
 
            QUATERNIONS[comp,:,:] = self._quaternions[comp][:,:]
            COM[comp,:,:] = self._coms[comp][:,:]
            FIT[comp,:] = self._fits[comp][:]
                         
        outputFile.close()