# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DL_POLY.py
# @brief     Implements module/class/test DL_POLY
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import re

import numpy

from MMTK import Atom, AtomCluster
from MMTK import Units
from MMTK.ParticleProperties import Configuration, ParticleVector
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import InfiniteUniverse, ParallelepipedicPeriodicUniverse

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converter import Converter
       
_HISTORY_FORMAT = {}
_HISTORY_FORMAT["2"] = {"rec1" : 81, "rec2" : 31, "reci" : 61, "recii" : 37, "reciii" : 37, "reciv" : 37, "reca" : 43, "recb" : 37, "recc" : 37, "recd" : 37}
_HISTORY_FORMAT["3"] = {"rec1" : 73, "rec2" : 73, "reci" : 73, "recii" : 73, "reciii" : 73, "reciv" : 73, "reca" : 73, "recb" : 73, "recc" : 73, "recd" : 73}
_HISTORY_FORMAT["4"] = {"rec1" : 73, "rec2" : 73, "reci" : 73, "recii" : 73, "reciii" : 73, "reciv" : 73, "reca" : 73, "recb" : 73, "recc" : 73, "recd" : 73}

class FieldFileError(Error):
    pass          

class HistoryFileError(Error):
    pass

class DL_POLYConverterError(Error):
    pass

class FieldFile(dict):

    def __init__(self, filename, aliases):
        
        self._filename = filename
        
        self._aliases = aliases
        
        self.parse()        
        
        
    def parse(self):

        # The FIELD file is opened for reading, its contents stored into |lines| and then closed.
        unit = open(self._filename, 'r')

        # Read and remove the empty and comments lines from the contents of the FIELD file.
        lines = [line.strip() for line in unit.readlines() if line.strip() and not re.match('#',line)]
    
        # Close the FIELD file.
        unit.close()

        self['title'] = lines.pop(0)

        self['units'] = lines.pop(0)

        # Extract the number of molecular types
        _, self['n_molecular_types'] = re.match("(molecules|molecular types)\s+(\d+)",lines.pop(0), re.IGNORECASE).groups()

        self['n_molecular_types'] = int(self['n_molecular_types'])

        molBlocks = [i for i,line in enumerate(lines) if re.match("finish", line, re.IGNORECASE)]
        
        if self['n_molecular_types'] != len(molBlocks):
            raise FieldFileError("Error in the definition of the molecular types")
    
        self['molecules'] = []
    
        first = 0
    
        for last in molBlocks:
        
            moleculeName = lines[first]
        
            # Extract the number of molecular types
            nMolecules = re.match("nummols\s+(\d+)",lines[first+1], re.IGNORECASE).groups()[0]
            nMolecules = int(nMolecules)
                
            for i in range(first+2,last):
                        
                match = re.match("atoms\s+(\d+)",lines[i], re.IGNORECASE)
                if match:

                    nAtoms = int(match.groups()[0])
                
                    sumAtoms = 0
                
                    comp = i+1

                    atoms = []
                
                    while (sumAtoms < nAtoms):
                                    
                        sitnam = lines[comp][:8].strip()
                    
                        vals = lines[comp][8:].split()

                        if self._aliases.has_key(sitnam):
                            element = self._aliases[sitnam]
                        else:
                            element = sitnam
                            while 1:
                                if ELEMENTS.has_element(element):
                                    break
                                element = element[:-1]
                                if not element:
                                    raise FieldFileError("Could not define any element from %r" % sitnam)
                                              
                        try:
                            nrept = int(vals[2])
                        except IndexError:
                            nrept = 1
                    
                        atoms.extend([(sitnam,element)]*nrept)
                                            
                        sumAtoms += nrept
                        
                        comp += 1
                    
                    self['molecules'].append([moleculeName,nMolecules,atoms])
                
                    break

            first = last + 1
        
    def build_mmtk_contents(self, universe=None):
                
        self._mmtkObjects = []
            
        for moleculeName, nMolecules, atomicContents in self["molecules"]:
            
            # Loops over the number of molecules of the current type.
            for _ in range(nMolecules):
                
                # This list will contains the MMTK instance of the atoms of the molecule.
                temp = []
                
                # Loops over the atom of the molecule.
                for i, (name, element) in enumerate(atomicContents):
                    # The atom is created.
                    a = Atom(element, name="%s%s" % (name,i))
                    temp.append(a)

                if len(temp) > 1:
                    temp = [AtomCluster(temp, name=moleculeName)]               
                
                self._mmtkObjects.append(temp[0])
                    
        if universe is not None:
            [universe.addObject(obj) for obj in self._mmtkObjects]
            
class HistoryFile(dict):
    
    def __init__(self, filename, version="2"):

        self['instance'] = open(filename, 'rb')

        testLine = len(self['instance'].readline())
        
        if (testLine not in [81,82]) and (testLine not in [73,74]):
            raise HistoryFileError('Invalid DLPOLY history file')

        self['instance'].seek(0,0)
        
        self["version"] = version
        
        offset = testLine - _HISTORY_FORMAT[self["version"]]["rec1"]

        self._headerSize = _HISTORY_FORMAT[self["version"]]["rec1"] + _HISTORY_FORMAT[self["version"]]["rec2"] + 2*offset

        self['instance'].read(_HISTORY_FORMAT[self["version"]]["rec1"]+offset)

        data = self['instance'].read(_HISTORY_FORMAT[self["version"]]["rec2"]+offset)
                                
        self["keytrj"], self["imcon"], self["natms"] = [int(v) for v in data.split()[0:3]] 
        
        if self["keytrj"] not in range(3):
            raise HistoryFileError("Invalid value for trajectory output key.")

        if self["imcon"] not in range(4):
            raise HistoryFileError("Invalid value for periodic boundary conditions key.")

        self._configHeaderSize = _HISTORY_FORMAT[self["version"]]["reci"] + 3*_HISTORY_FORMAT[self["version"]]["recii"] + 4*offset
        
        self._configSize = (_HISTORY_FORMAT[self["version"]]["reca"] + offset + (self["keytrj"]+1)*(_HISTORY_FORMAT[self["version"]]["recb"]+offset))*self["natms"]

        self._frameSize = self._configHeaderSize + self._configSize
        
        self['instance'].seek(0,2)

        self["n_frames"] = (self['instance'].tell()-self._headerSize)/self._frameSize
        
        self['instance'].seek(self._headerSize)

        data = self['instance'].read(self._configHeaderSize).splitlines()
              
        line = data[0].split()
              
        self._firstStep = int(line[1])

        self._timeStep = float(line[5])

        self._maskStep = 3+3*(self["keytrj"]+1)+1
        
        if (self["version"] == u'3') or (self["version"] == u'4'):
            self._maskStep += 1
        
        self['instance'].seek(0)        
                        
    def read_step(self, step):

        self['instance'].seek(self._headerSize+step*self._frameSize)

        data = self['instance'].read(self._configHeaderSize).splitlines()
        
        line = data[0].split()
        
        currentStep = int(line[1])
        
        timeStep = (currentStep - self._firstStep)*self._timeStep
        
        cell = " ".join(data[1:]).split()

        cell = numpy.array(cell,dtype=numpy.float64)
        
        cell = numpy.reshape(cell,(3,3))*Units.Ang
                
        data = numpy.array(self['instance'].read(self._configSize).split())
        
        mask = numpy.ones((len(data),), dtype=numpy.bool)
        mask[0::self._maskStep] = False
        mask[1::self._maskStep] = False
        mask[2::self._maskStep] = False
        mask[3::self._maskStep] = False
        if (self["version"] == u'3') or (self["version"] == u'4'):
            mask[4::self._maskStep] = False

        config = numpy.array(numpy.compress(mask,data),dtype=numpy.float64)

        config = numpy.reshape(config,(self["natms"],3*(self["keytrj"]+1)))
                
        config[:,0:3] *= Units.Ang
        
        if self["keytrj"] == 1:
            config[:,3:6] *= Units.Ang/Units.ps
            
        elif self["keytrj"] == 2:
            config[:,3:6] *= Units.Ang/Units.ps
            config[:,6:9] *= -Units.amu*Units.Ang/Units.ps**2

        return timeStep, cell, config
    
    def close(self):
        self["instance"].close()
                                           
class DL_POLYConverter(Converter):
    """
    Converts a DL_POLY trajectory to a MMTK trajectory.
    """
    
    label = "DL-POLY"

    settings = collections.OrderedDict()   
    settings['field_file'] = ('input_file',{'wildcard':"FIELD files|FIELD*|All files|*",
                                            'default':os.path.join('..','..','..','Data','Trajectories','DL_Poly','FIELD_cumen')})
    settings['history_file'] = ('input_file',{'wildcard':"HISTORY files|HISTORY*|All files|*",
                                              'default':os.path.join('..','..','..','Data','Trajectories','DL_Poly','HISTORY_cumen')})
    settings['atom_aliases'] = ('python_object',{'default':{}})
    settings['version'] = ('single_choice', {'choices':_HISTORY_FORMAT.keys(), 'default':'2'})
    settings['output_file'] = ('single_output_file', {'format':"netcdf",'root':'field_file'})
                    
    def initialize(self):
        '''
        Initialize the job.
        '''
        
        self._atomicAliases = self.configuration["atom_aliases"]["value"]
        
        self._fieldFile = FieldFile(self.configuration["field_file"]["filename"], aliases=self._atomicAliases)
        
        self._historyFile = HistoryFile(self.configuration["history_file"]["filename"], self.configuration["version"]["value"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._historyFile['n_frames']
                
        if self._historyFile["imcon"] == 0:
            self._universe = InfiniteUniverse()

        else:
            self._universe = ParallelepipedicPeriodicUniverse()
             
        self._fieldFile.build_mmtk_contents(self._universe)

        self._velocities = None
        
        self._gradients = None
                                
        data_to_be_written = ['configuration','time']
        if self._historyFile["keytrj"] == 1:
            self._universe.initializeVelocitiesToTemperature(0.)
            self._velocities = ParticleVector(self._universe)
            data_to_be_written.append('velocities')
            
        elif self._historyFile["keytrj"] == 2:
            self._universe.initializeVelocitiesToTemperature(0.)
            self._velocities = ParticleVector(self._universe)
            self._gradients = ParticleVector(self._universe)
            data_to_be_written.extend(['velocities','gradients'])
                                    
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['file'], mode='w', comment=self._fieldFile["title"])

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, data_to_be_written, 0, None, 1)])
        
    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """
                                                
        # The x, y and z values of the current frame.
        time, cell, config = self._historyFile.read_step(index)
        
        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        if self._universe.is_periodic:
            self._universe.setShape(cell)
                    
        self._universe.setConfiguration(Configuration(self._universe, config[:,0:3]))
                   
        self._universe.foldCoordinatesIntoBox()
        
        data = {"time" : time}
        
        if self._velocities is not None:
            self._velocities.array = config[:,3:6]
            data["velocities"] = self._velocities

        if self._gradients is not None:
            self._gradients.array = config[:,6:9]
            data["gradients"] = self._gradients

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
        
        self._historyFile.close()

        # Close the output trajectory.
        self._trajectory.close()
                
REGISTRY['dl_poly'] = DL_POLYConverter
