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
Created on Apr 10, 2015

:author: Eric C. Pellegrini
'''

import collections
import os
import re

import numpy

from MMTK import Atom, AtomCluster
from MMTK import Units
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import ParallelepipedicPeriodicUniverse

from MDANSE import ELEMENTS
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converters.Converter import Converter
from MDANSE.Mathematics.Graph import Graph

class LAMMPSConfigFileError(Error):
    pass

class LAMMPSTrajectoryFileError(Error):
    pass

class LAMMPSConfigFile(dict):

    def __init__(self, filename):
        
        self._filename = filename

        self['n_bonds'] = None

        self['bonds'] = []
                
        self['n_atoms'] = None
        
        self["n_atom_types"] = None
        
        self["elements"] = {}
                
        unit = open(self._filename, 'r')
        lines = []
        for l in unit.readlines():
            l = l.strip()
            if l:
                lines.append(l)        
        unit.close()
    
        for i, line in enumerate(lines):
                                        
            if self['n_atoms'] is None:
                m = re.match("^(\d+) atoms$",line, re.I) 
                if m:
                    self['n_atoms'] = int(m.groups()[0])
                  
            if self["n_atom_types"] is None: 
                m = re.match("^(\d+) atom types$",line, re.I)             
                if m:
                    self["n_atom_types"] = int(m.groups()[0])

            if self['n_bonds'] is None:
                m = re.match("^(\d+) bonds$",line, re.I) 
                if m:
                    self['n_bonds'] = int(m.groups()[0])

            if re.match("^masses$", line, re.I):
                
                if self["n_atom_types"] is None:
                    raise LAMMPSConfigFileError("Did not find the number of atom types.")
                                                                    
                for j in range(1, self["n_atom_types"]+1):
                    idx, mass = lines[i+j].strip().split()
                    el = ELEMENTS.match_numeric_property("atomic_weight", float(mass), tolerance=1.0e-3)
                    self["elements"][idx] = el[0]

            m = re.match("^bonds$",line, re.I)
            if m:
                for j in range(1, self['n_bonds']+1):
                    _,_,at1,at2 = lines[i+j].split()
                    at1 = int(at1)-1
                    at2 = int(at2)-1
                    self['bonds'].append([at1,at2])
                self['bonds'] = numpy.array(self['bonds'], dtype=numpy.int32)
                                                   
        unit.close()

                
class LAMMPSConverter(Converter):
    """
    Converts a LAMMPS trajectory to a MMTK trajectory.
    """
              
    type = 'lammps'
    
    label = "LAMMPS"

    settings = collections.OrderedDict()        
    settings['config_file'] = ('input_file', {'label':"LAMMPS configuration file",
                                              'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.config')})
    settings['trajectory_file'] = ('input_file', {'label':"LAMMPS trajectory file",
                                                  'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.lammps')})
    settings['time_step'] = ('float', {'label':"time step (fs)", 'default':1.0, 'mini':1.0e-9})        
    settings['n_steps'] = ('integer', {'label':"number of time steps", 'default':1, 'mini':0})        
    settings['output_file'] = ('output_files', {'formats':["netcdf"]})
    
    def initialize(self):
        '''
        Initialize the job.
        '''
                
        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]
        
        self._lammpsConfig = LAMMPSConfigFile(self.configuration["config_file"]["value"])
        
        self.parse_first_step()
        
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['files'][0], mode='w')

        self._nameToIndex = dict([(at.name,at.index) for at in self._universe.atomList()])

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])

        self._lammps.seek(0,0)

        self._start = 0

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        for _ in range(self._itemsPosition["TIMESTEP"][0]):
            line = self._lammps.readline()
            if not line:
                return index, None

        timeStep = Units.fs*float(self._lammps.readline())*self.configuration['time_step']['value']

        for _ in range(self._itemsPosition["TIMESTEP"][1], self._itemsPosition["BOX BOUNDS"][0]):
            self._lammps.readline()

        abcVectors = numpy.zeros((9), dtype=numpy.float64)
        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            xlo, xhi = temp
            xy = 0.0
        elif len(temp) == 3:
            xlo, xhi, xy = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for A vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            ylo, yhi = temp
            xz = 0.0
        elif len(temp) == 3:
            ylo, yhi, xz = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for B vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            zlo, zhi = temp
            yz = 0.0
        elif len(temp) == 3:
            zlo, zhi, yz = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for C vector components")
                      
        # The ax component.                                      
        abcVectors[0] = xhi - xlo
        
        # The bx and by components.                                      
        abcVectors[3] = xy
        abcVectors[4] = yhi - ylo
        
        # The cx, cy and cz components.                                      
        abcVectors[6] = xz
        abcVectors[7] = yz
        abcVectors[8] = zhi - zlo

        abcVectors *= Units.Ang

        for _ in range(self._itemsPosition["BOX BOUNDS"][1], self._itemsPosition["ATOMS"][0]):
            self._lammps.readline()

        self._universe.setCellParameters(abcVectors)

        conf = self._universe.configuration()

        for i,_ in enumerate(range(self._itemsPosition["ATOMS"][0], self._itemsPosition["ATOMS"][1])):
            temp = self._lammps.readline().split()
            idx = self._nameToIndex[self._rankToName[i]]
            conf.array[idx,:] = numpy.array([temp[self._x],temp[self._y],temp[self._z]],dtype=numpy.float64)

        if self._fractionalCoordinates:
            conf.array = self._universe._boxToRealPointArray(conf.array)
        else:
            conf.array *= Units.Ang
            
        # The whole configuration is folded in to the simulation box.
        self._universe.foldCoordinatesIntoBox()

        # A snapshot is created out of the current configuration.
        self._snapshot(data = {'time': timeStep})

        self._start += self._last
        
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
        
        self._lammps.close()

        if self._lammpsConfig["n_bonds"] is not None:
            netcdf = self._trajectory.trajectory.file
            netcdf.createDimension("MDANSE_NBONDS",self._lammpsConfig["n_bonds"])
            netcdf.createDimension("MDANSE_TWO",2)
            VAR = netcdf.createVariable("mdanse_bonds", numpy.dtype(numpy.int32).char, ("MDANSE_NBONDS","MDANSE_TWO"))
            VAR.assignValue(self._lammpsConfig["bonds"]) 
                
        # Close the output trajectory.
        self._trajectory.close()
                        
    def parse_first_step(self):

        self._lammps = open(self.configuration["trajectory_file"]["value"], 'r')        

        self._itemsPosition = collections.OrderedDict()

        self._universe = None
        comp = -1

        while True:

            line = self._lammps.readline()
            comp += 1

            if not line:
                break

            if line.startswith("ITEM: TIMESTEP"):
                self._itemsPosition["TIMESTEP"] = [comp+1, comp+2]
                continue

            elif line.startswith("ITEM: BOX BOUNDS"):
                self._itemsPosition["BOX BOUNDS"] = [comp+1, comp+4]
                continue

            elif line.startswith("ITEM: ATOMS"):
                
                keywords = line.split()[2:]
                
                self._id = keywords.index("id")
                self._type = keywords.index("type")
                
                try:
                    self._x = keywords.index("x")
                    self._y = keywords.index("y")
                    self._z = keywords.index("z")
                except ValueError:
                    try:
                        self._x = keywords.index("xs")
                        self._y = keywords.index("ys")
                        self._z = keywords.index("zs")
                    except ValueError:
                        raise LAMMPSTrajectoryFileError("No coordinates could be found in the trajectory")
                    else:
                        self._fractionalCoordinates = True
                        
                else:
                    self._fractionalCoordinates = False
                    
                self._rankToName = {}
                
                g = Graph()
                self._universe = ParallelepipedicPeriodicUniverse()
                self._itemsPosition["ATOMS"] = [comp+1,comp+self._nAtoms+1]                                
                for i in range(self._nAtoms):
                    temp = self._lammps.readline().split()
                    idx = int(temp[self._id])-1
                    ty = temp[self._type]
                    name = "%s%s" % (self._lammpsConfig["elements"][ty],idx)
                    self._rankToName[i] = name
                    g.add_node(idx, element=self._lammpsConfig["elements"][ty], atomName=name)
                    
                if self._lammpsConfig["n_bonds"] is not None:
                    for idx1,idx2 in self._lammpsConfig["bonds"]:
                        g.add_link(idx1,idx2)
                
                for cluster in g.build_connected_components():
                    if len(cluster) == 1:
                        node = cluster.pop()
                        obj = Atom(node.element, name=node.atomName)
                        obj.index = node.name
                    else:
                        atList = []
                        for atom in cluster:
                            at = Atom(atom.element, name=atom.atomName)
                            atList.append(at) 
                        c = collections.Counter([at.element for at in cluster])
                        name = "".join(["%s%d" % (k,v) for k,v in sorted(c.items())])
                        obj = AtomCluster(atList, name=name)
                        
                    self._universe.addObject(obj)
                self._last = comp + self._nAtoms + 1

                break
                    
            elif line.startswith("ITEM: NUMBER OF ATOMS"):
                self._nAtoms = int(self._lammps.readline())
                comp += 1
                continue            