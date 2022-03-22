# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Generic.py
# @brief     Implements module/class/test Generic
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os

import numpy

from MMTK import Atom, AtomCluster
from MMTK.ParticleProperties import Configuration, ParticleVector
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import InfiniteUniverse, ParallelepipedicPeriodicUniverse

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converter import Converter
                 
class GenericConverterError(Error):
    pass
                                                  
class GenericConverter(Converter):
    """
    Converts a trajectory written in ASCII to a MMTK trajectory file.
    
    This converter can be useful when using MD packages that are currently not supported by MDANSE. 
    
    Here is an example of ASCII trajectory that can be converted using this converter to a MMTk trajectory.
    
    MOLECULAR_CONTENTS
    2
    
    ETHYNE
    C1 C
    C2 C
    H2 H
    H2 H
    
    WATER
    O1 O
    H1 H
    H2 H
    
    MOLECULES
    ETHYNE 1
    WATER 2
    
    NSTEPS
    4
    
    TIMESTEP
    10
    
    STEP
    10
    
    CELL
    10,0,0
    0,10,0
    0,0,10
    
    CONFIGURATION
    0,0,0
    0,0,1
    0,1,0
    0,1,1
    1,0,0
    1,0,1
    1,1,0
    1,1,1
    2,2,2
    3,3,3
    
    STEP
    20
    
    CELL
    10,0,0
    0,10,0
    0,0,10
    
    CONFIGURATION
    0,0,0
    0,0,1
    0,1,0
    0,1,1
    1,0,0
    1,0,1
    1,1,0
    1,1,1
    2,2,2
    3,3,3
    
    STEP
    30
    
    CELL
    10,0,0
    0,10,0
    0,0,10
    
    CONFIGURATION
    0,0,0
    0,0,1
    0,1,0
    0,1,1
    1,0,0
    1,0,1
    1,1,0
    1,1,1
    2,2,2
    3,3,3
    
    STEP
    40
    
    CELL
    10,0,0
    0,10,0
    0,0,10
    
    CONFIGURATION
    0,0,0
    0,0,1
    0,1,0
    0,1,1
    1,0,0
    1,0,1
    1,1,0
    1,1,1
    2,2,2
    3,3,3

    """
    
    label = "Generic"

    settings = collections.OrderedDict()   
    settings['gt_file'] = ('input_file',{'wildcard':"Generic trajectory files|*.gtf|All files|*",
                                         'default':os.path.join('..','..','..','Data','Trajectories','Generic','test.gtf')})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                    
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
        if self._gtFile.readline().strip() != "NFRAMES":
            raise GenericConverterError("Invalid keyword#3: must be 'NFRAMES'")         
        try:
            self.numberOfSteps=int(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError("Invalid type for 'NFRAMES' keyword. Must be an integer corresponding to the number of frames of the simulation.")

        # Read a blank line
        self._gtFile.readline()

        # Read the time step
        if self._gtFile.readline().strip() != "FRAMETIME":
            raise GenericConverterError("Invalid keyword#4: must be 'FRAMETIME'")
        try:
            self._timeStep=float(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError("Invalid type for 'FRAMETIME' keyword. Must be a float corresponding to the time between two frames of the simulation.")

        # Read a blank line
        self._gtFile.readline()

        # Read the box coordinates
        if self._gtFile.readline().strip() != "BOX_COORDINATES":
            raise GenericConverterError("Invalid keyword#5: must be 'BOX_COORDINATES'")
        try:
            self._box=bool(self._gtFile.readline())
        except ValueError:
            raise GenericConverterError("Invalid type for 'BOX_COORDINATES' keyword. Must be a boolean indicating whether or not the coordinates are in box.")
        
        # Read a blank line
        self._gtFile.readline()

        self._headerBlockSize=self._gtFile.tell()
        
        # Read the beginning of the first frame to define the size of various data block
        
        self._pbc = []
        if self._gtFile.readline().strip() == "CELL":
            
            for _ in range(self.numberOfSteps):
                cell = numpy.array([self._gtFile.readline().strip().split(",") for _ in range(3)],dtype=numpy.float64)
                if cell.shape != (3,3):
                    raise GenericConverterError('Invalid cell shape. Must be a 3x3 matrix.')
                self._pbc.append(cell)
                    
                # Read a blank line
                self._gtFile.readline()
                
                pos = self._gtFile.tell()
                            
                if self._gtFile.readline().strip == "CONFIGURATION":
                    break
                else:
                    self._gtFile.seek(pos,0)
                    
        if self._pbc:                         
            self._universe = ParallelepipedicPeriodicUniverse()
            # Case of NVT simulation
            if len(self._pbc)==1:
                self._universe.setShape(self._pbc.pop(0))
            else:
                if len(self._pbc) != self.numberOfSteps:
                    raise GenericConverterError('Invalid number of cell definitions. Must be equal to the number of frames for a NPT simulation.')      
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
                            
        # Read the current configuration
        if self._gtFile.readline().strip() != "CONFIGURATION":
            raise GenericConverterError("Invalid frame block. Must contain 'CONFIGURATION' keyword.")

        pos = self._gtFile.tell()
        
        line=self._gtFile.readline()
        line=line.split(',')
        n=len(line)
        self._hasVelocities=False
        self._hasForces=False
        if n==6:
            self._hasVelocities=True
            self._hasForces=False
        elif n==9:
            self._hasVelocities=True
            self._hasForces=True          
        
        self._gtFile.seek(pos,0)
        
        if self._hasVelocities:
            self._universe.initializeVelocitiesToTemperature(0.0)
            self._velocities = ParticleVector(self._universe)
            if self._hasForces:        
                self._forces = ParticleVector(self._universe)
                self._dataShape=(self._universe.numberOfAtoms(),9)
            else:
                self._dataShape=(self._universe.numberOfAtoms(),6)
        else:
            self._dataShape=(self._universe.numberOfAtoms(),3)
                                    
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_files']['files'][0], mode='w')
 
        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])
            
    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """
                        
        if self._pbc:                    
            self._universe.setShape(self._pbc[index])
                        
        config = numpy.array([self._gtFile.readline().split(",") for _ in range(self._universe.numberOfAtoms())],dtype=numpy.float64)
        if config.shape != self._dataShape:
            raise GenericConverterError('Invalid data shape. Must be a %s matrix.' % (self._dataShape,))

        # Read a junk line
        self._gtFile.readline()
        
        conf = Configuration(self._universe, config[:,0:3])
        if self._box:
            conf.convertFromBoxCoordinates()
        
        self._universe.setConfiguration(conf)
        
        self._universe.foldCoordinatesIntoBox()
                
        data = {"time" : index*self._timeStep}
        
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
                
REGISTRY['generic'] = GenericConverter
