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
Created on Jun 08, 2015

@author: Eric C. Pellegrini
'''

import collections

import numpy

from MMTK import Atom, AtomCluster
from MMTK.ParticleProperties import Configuration, ParticleVector
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import InfiniteUniverse, ParallelepipedicPeriodicUniverse

from MDANSE import ELEMENTS
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converters.Converter import Converter
                 
class GenericConverterError(Error):
    pass
                                                  
class GenericConverter(Converter):
    """
    """

    type = 'generic'
    
    label = "Generic"

    category = ('Converters',)
    
    ancestor = None

    settings = collections.OrderedDict()   
    settings['gt_file'] = ('input_file',{'wildcard':"Generic trajectory files|*.gtf|All files|*"})
    settings['output_file'] = ('output_files', {'formats':["netcdf"]})
                    
    def initialize(self):
        '''
        Initialize the job.
        '''

        self._gtFile = open(self.configuration["gt_file"]["filename"], 'rb')

        if self._gtFile.readline().strip() != "MOLECULAR_CONTENTS":
            raise GenericConverterError("Invalid keyword #1. Must be 'MOLECULAR_CONTENTS'")

        # Read the number of molecular types that define the universe        
        try:
            nMolecularTypes=int(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError("Invalid type for 'MOLECULAR_CONTENTS' keyword. Must be an integer corresponding to the number of molecular types found in the simulation.")

        # Blank line
        self._gtFile.readline()

        self._molecularTypes = collections.OrderedDict()
        
        for _ in range(nMolecularTypes):
            molName = self._gtFile.readline().strip()
            if self._molecularTypes.has_key(molName):
                raise GenericConverterError("Duplicate molecule name.")
            self._molecularTypes[molName] = []
            line = self._gtFile.readline().strip()
            while line: 
                atomName, atomType = line.split()
                if not atomType in ELEMENTS:
                    raise GenericConverterError("Unknown atom type: %s" % atomType)
                self._molecularTypes[molName].append((atomName,atomType))                
                line = self._gtFile.readline().strip()

        if self._gtFile.readline().strip() != "MOLECULES":
            raise GenericConverterError("Invalid keyword #2. Must be 'MOLECULES'")
        
        self._molecules = []
        line=self._gtFile.readline().strip()
        while line:
            molName,nMols=line.strip().split()
            if not self._molecularTypes.has_key(molName):
                raise GenericConverterError("Unknown molecule name: %s" % molName)
            try:
                nMols = int(nMols)
            except ValueError:
                raise GenericConverterError("Invalid type for the number of atoms in molecule %s. Must be an integer." % molName);
            
            self._molecules.append((molName,nMols))
            
            line=self._gtFile.readline().strip()
                                 
        # Read the number of steps
        if self._gtFile.readline().strip() != "NSTEPS":
            raise GenericConverterError("Invalid keyword#4: must be 'NSTEPS'")         
        try:
            self.numberOfSteps=int(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError("Invalid type for 'NSTEPS' keyword. Must be an integer corresponding to the number of steps of the simulation.")

        # Read a blank line
        self._gtFile.readline()

        # Read the number of steps
        if self._gtFile.readline().strip() != "TIMESTEP":
            raise GenericConverterError("Invalid keyword#5: must be 'TIMESTEP'")
         
        # Read the time step        
        try:
            self._timeStep=float(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError("Invalid type for 'TIMESTEP' keyword. Must be a float corresponding to the actual timestep of the simulation.")

        # Read a blank line
        self._gtFile.readline()

        self._headerBlockSize=self._gtFile.tell()
        
        # Read the first frame to define the size of various data block

        # Read the current step number
        if self._gtFile.readline().strip() != "STEP":
            raise GenericConverterError("Invalid frame block. Must start with 'STEP' keyword.")
        try:
            _=int(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError("Invalid type for 'STEP' keyword. Must be a in corresponding to the current step number of the simulation.")
                    
        # Read a blank line
        self._gtFile.readline()

        self._pbc = (self._gtFile.readline().strip() == "CELL")
                        
        if self._pbc:
            self._universe = ParallelepipedicPeriodicUniverse()
            pos = self._gtFile.tell()
            self._gtFile.readline()
            self._gtFile.readline()
            self._gtFile.readline()
            self._cellBlockSize=self._gtFile.tell()-pos
        else:
            self._universe = InfiniteUniverse()

        for molName,nMols in self._molecules:
             
            for _ in range(nMols):
                molType = self._molecularTypes[molName]
 
                temp = [Atom(atomType,name=atomName) for atomName,atomType in molType]
                 
                if len(temp)==1:
                    self._universe.addObject(temp[0])
                else:
                    self._universe.addObject(AtomCluster(temp,name=molName))
                    
        # Read a blank line
        self._gtFile.readline()
        
        # Read the current configuration
        if self._gtFile.readline().strip() != "CONFIGURATION":
            raise GenericConverterError("Invalid frame block. Must contain 'CONFIGURATION' keyword.")
        
        pos = self._gtFile.tell()
        
        for _ in range(self._universe.numberOfAtoms()):
            line=self._gtFile.readline()
        self._dataBlockSize=self._gtFile.tell()-pos
        line=line.split(',')
        n=len(line)
        if n==3:
            self._hasVelocities=False
            self._hasForces=False
        elif n==6:
            self._hasVelocities=True
            self._hasForces=False
        elif n==9:
            self._hasVelocities=True
            self._hasForces=True          
        else:
            raise GenericConverterError("Invalid configuration line. Must contain3, 6 0r 9 comma-separated fixed-formatted floats.")
        
        # Read a blank line
        self._gtFile.readline()
        
        if (self._hasVelocities or self._hasForces):
            self._universe.initializeVelocitiesToTemperature(0.0)
            self._velocities = ParticleVector(self._universe)
        
        if self._hasForces:
            self._forces = ParticleVector(self._universe)
                                    
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['files'][0], mode='w')
 
        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])
        
        self._frameBlockSize = self._gtFile.tell() - self._headerBlockSize
    
    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """
        
        self._gtFile.seek(self._headerBlockSize+index*self._frameBlockSize)
        
        # Read a blank line
        self._gtFile.readline()
        try:
            step=int(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError('Invalid step number value.')

        if self._pbc:        
            # Read two junk lines
            self._gtFile.readline()
            self._gtFile.readline()
            
            cell = numpy.array([v.split(",") for v in self._gtFile.read(self._cellBlockSize).splitlines()],dtype=numpy.float64)
            
            if cell.shape != (3,3):
                raise GenericConverterError('Invalid cell data.')
            
            self._universe.setShape(cell)
            
        # Read two junk lines
        self._gtFile.readline()
        self._gtFile.readline()
            
        config = numpy.array([v.split(",") for v in self._gtFile.read(self._dataBlockSize).splitlines()],dtype=numpy.float64)
        
        self._universe.setConfiguration(Configuration(self._universe, config[:,0:3]))
        
        self._universe.foldCoordinatesIntoBox()
        
        data = {"time" : step*self._timeStep}
        
        if self._hasVelocities:
            self._velocities.array = config[:,3:6]
            self._universe.setVelocities(self._velocities)

        if self._hasForces:
            self._forces.array = config[:,6:9]
            data["forces"] = self._forces
                             
        # Store a snapshot of the current configuration in the output trajectory.
        self._snapshot(data=data)
                                                                        
        return index, None
        
    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x:
        @type x: any.
        """
        
        pass
    
    def finalize(self):
        """
        Finalize the job.
        """
        
        self._gtFile.close()

        # Close the output trajectory.
        self._trajectory.close()
                
