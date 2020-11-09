# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/LAMMPS.py
# @brief     Implements module/class/test LAMMPS
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
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import ParallelepipedicPeriodicUniverse

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converter import Converter
from MDANSE.Mathematics.Graph import Graph

class LAMMPSConfigFileError(Error):
    pass

class LAMMPSTrajectoryFileError(Error):
    pass

class LAMMPSConfigFile(dict):

    def __init__(self, filename,tolerance,smart_association):
        
        self._filename = filename
        
        self._tolerance = tolerance

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
                m = re.match("^\s*(\d+)\s*atoms\s*$",line, re.I) 
                if m:
                    self['n_atoms'] = int(m.groups()[0])
                  
            if self["n_atom_types"] is None: 
                m = re.match("^\s*(\d+)\s*atom types\s*$",line, re.I)             
                if m:
                    self["n_atom_types"] = int(m.groups()[0])

            if self['n_bonds'] is None:
                m = re.match("^\s*(\d+)\s*bonds\s*$",line, re.I) 
                if m:
                    self['n_bonds'] = int(m.groups()[0])

            if re.match("^\s*masses\s*$", line, re.I):
                
                if self["n_atom_types"] is None:
                    raise LAMMPSConfigFileError("Did not find the number of atom types.")
                                                                    
                for j in range(1, self["n_atom_types"]+1):
                    data_line = lines[i+j].strip().split("#")[0] #Remove commentary if any
                    idx, mass = data_line.split()[0:2]
                    idx = int(idx)
                    mass = float(mass)
                    el = ELEMENTS.match_numeric_property("atomic_weight", mass, tolerance=self._tolerance)
                    nElements = len(el)
                    if nElements == 0:
                        # No element is matching
                        raise LAMMPSConfigFileError("The atom %d with defined mass %f could not be assigned with a tolerance of %f. Please modify the mass in the config file to comply with MDANSE internal database" % (idx,mass,self._tolerance))
                    elif nElements == 1:
                        # One element is matching => continue
                        self["elements"][idx] = el[0]
                    elif nElements == 2 and el[0][:min((len(el[0]), len(el[1])))] == el[1][:min((len(el[0]), len(el[1])))]:
                        # If two elements are matching, these can be the same appearing twice (example 'Al' and 'Al27')
                        self["elements"][idx] = el[0]
                    else:
                        # Two or more elements are matching
                        if smart_association:
                            # Take the nearest match
                            matched_element = None
                            for element in el:
                                if matched_element is None:
                                    matched_element=element
                                else:
                                    if numpy.abs(ELEMENTS[element]["atomic_weight"] - mass) < numpy.abs(ELEMENTS[matched_element]["atomic_weight"] - mass):
                                        matched_element = element
                            self["elements"][idx] = matched_element
                            print(matched_element)
                        else:
                            # More than two elements are matching => error
                            raise LAMMPSConfigFileError("The atoms %s of MDANSE database matches the mass %f with a tolerance of %f. Please modify the mass in the config file to comply with MDANSE internal database" % (el,mass,self._tolerance))

            m = re.match("^\s*bonds\s*$",line, re.I)
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
                  
    label = "LAMMPS"

    settings = collections.OrderedDict()        
    settings['config_file'] = ('input_file', {'label':"LAMMPS configuration file",
                                              'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.config')})
    settings['trajectory_file'] = ('input_file', {'label':"LAMMPS trajectory file",
                                                  'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.lammps')})
    settings['mass_tolerance'] = ('float', {'label':"mass tolerance (uma)", 'default':1.0e-3, 'mini':1.0e-9})
    settings['smart_mass_association'] = ('boolean', {'label':"smart mass association", 'default':True})
    settings['time_step'] = ('float', {'label':"time step (fs)", 'default':1.0, 'mini':1.0e-9})        
    settings['n_steps'] = ('integer', {'label':"number of time steps (0 for automatic detection)", 'default':0, 'mini':0})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
    
    def initialize(self):
        '''
        Initialize the job.
        '''
                
        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]
        
        self._lammpsConfig = LAMMPSConfigFile(self.configuration["config_file"]["value"],self.configuration["mass_tolerance"]["value"],self.configuration['smart_mass_association']["value"])
        
        self.parse_first_step()
        
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_files']['files'][0], mode='w')

        self._nameToIndex = dict([(at.name,at.index) for at in self._universe.atomList()])

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])

        # Estimate number of steps if needed
        if self.numberOfSteps == 0:
            self.numberOfSteps = 1
            for line in self._lammps:
                if line.startswith("ITEM: TIMESTEP"):
                    self.numberOfSteps += 1

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
            idx = self._nameToIndex[self._rankToName[int(temp[0])-1]]
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
                
                # Field name is <x,y,z> or cd ..<x,y,z>u if real coordinates and <x,y,z>s if fractional ones
                self._fractionalCoordinates = False
                try:
                    self._x = keywords.index("x")
                    self._y = keywords.index("y")
                    self._z = keywords.index("z")
                except ValueError:
                    try:
                        self._x = keywords.index("xu")
                        self._y = keywords.index("yu")
                        self._z = keywords.index("zu")
                    except ValueError:
                        try:
                            self._x = keywords.index("xs")
                            self._y = keywords.index("ys")
                            self._z = keywords.index("zs")
                            self._fractionalCoordinates = True
                        except ValueError:
                            raise LAMMPSTrajectoryFileError("No coordinates could be found in the trajectory")
                    
                self._rankToName = {}
                
                g = Graph()
                self._universe = ParallelepipedicPeriodicUniverse()
                self._itemsPosition["ATOMS"] = [comp+1,comp+self._nAtoms+1]                                
                for i in range(self._nAtoms):
                    temp = self._lammps.readline().split()
                    idx = int(temp[self._id])-1
                    ty = int(temp[self._type])
                    name = "%s%d" % (self._lammpsConfig["elements"][ty],idx)
                    self._rankToName[int(temp[0])-1] = name
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
            
REGISTRY['lammps'] = LAMMPSConverter
            
