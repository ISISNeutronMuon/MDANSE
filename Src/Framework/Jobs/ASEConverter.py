# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/ASEConverter.py
# @brief     Implements a general-purpose loader based on ASE
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import re
from os.path import expanduser

from ase.io import iread
import numpy as np

from MDANSE import REGISTRY
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converter import Converter, InteractiveConverter
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration, PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class ASETrajectoryFileError(Error):
    pass

                
class ASEConverter(Converter):
    """
    Converts any trajectory to a HDF trajectory using the ASE io module.
    """
                  
    label = "ASE"

    settings = collections.OrderedDict()
    settings['trajectory_file'] = ('input_file', {'label':"Any MD trajectory file",
                                                  'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.lammps')})
    settings['configuration_file'] = ('input_file', {'label':"An optional structure/configuration file",
                                                  'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.lammps')})
    settings['time_step'] = ('float', {'label':"time step (fs)", 'default':1.0, 'mini':1.0e-9})      
    settings['time_unit'] = ('single_choice', {'label':"time step unit", 'choices':['fs','ps','ns'], 'default':'fs'})    
    settings['n_steps'] = ('integer', {'label':"number of time steps (0 for automatic detection)", 'default':0, 'mini':0})
    settings['output_file'] = ('single_output_file', {'format':"hdf",'root':'config_file'})
    
    def initialize(self):
        '''
        Initialize the job.
        '''
                
        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self.parse_first_step()

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration['output_file']['file'],
            self._chemicalSystem,
            self.numberOfSteps)

        self._nameToIndex = dict([(at.name,at.index) for at in self._trajectory.chemical_system.atom_list()])

        self._start = 0

        float(self.configuration['time_step']['value'])*measure(1.0,self.configuration['time_unit']['value'])

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        self._input = iread(self.configuration["trajectory_file"]["value"])

        for stepnum, frame in enumerate(self._input):
            time = stepnum * self._timestep

        for _ in range(self._itemsPosition["TIMESTEP"][0]):
            line = self._lammps.readline()
            if not line:
                return index, None

        time = float(self._lammps.readline())*self.configuration['time_step']['value']*measure(1.0,'fs').toval('ps')

        for _ in range(self._itemsPosition["TIMESTEP"][1], self._itemsPosition["BOX BOUNDS"][0]):
            self._lammps.readline()

        unitCell = np.zeros((9), dtype=np.float64)
        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            xlo, xhi = temp
            xy = 0.0
        elif len(temp) == 3:
            xlo, xhi, xy = temp
        else:
            raise ASETrajectoryFileError("Bad format for A vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            ylo, yhi = temp
            xz = 0.0
        elif len(temp) == 3:
            ylo, yhi, xz = temp
        else:
            raise ASETrajectoryFileError("Bad format for B vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            zlo, zhi = temp
            yz = 0.0
        elif len(temp) == 3:
            zlo, zhi, yz = temp
        else:
            raise ASETrajectoryFileError("Bad format for C vector components")
                      
        # The ax component.                                      
        unitCell[0] = xhi - xlo
        
        # The bx and by components.                                      
        unitCell[3] = xy
        unitCell[4] = yhi - ylo
        
        # The cx, cy and cz components.                                      
        unitCell[6] = xz
        unitCell[7] = yz
        unitCell[8] = zhi - zlo

        unitCell = np.reshape(unitCell,(3,3))

        unitCell *= measure(1.0,'ang').toval('nm')
        unitCell = UnitCell(unitCell)

        for _ in range(self._itemsPosition["BOX BOUNDS"][1], self._itemsPosition["ATOMS"][0]):
            self._lammps.readline()

        coords = np.empty((self._trajectory.chemical_system.number_of_atoms(),3),dtype=np.float)

        for i,_ in enumerate(range(self._itemsPosition["ATOMS"][0], self._itemsPosition["ATOMS"][1])):
            temp = self._lammps.readline().split()
            idx = self._nameToIndex[self._rankToName[int(temp[0])-1]]
            coords[idx,:] = np.array([temp[self._x],temp[self._y],temp[self._z]],dtype=np.float)

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system,
                coords,
                unitCell)
            realConf = conf.to_real_configuration()
        else:
            coords *= measure(1.0,'ang').toval('nm')
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system,
                coords,
                unitCell
            )
            
        if self.configuration['fold']['value']:
            # The whole configuration is folded in to the simulation box.
            realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(time,units={'time':'ps','unit_cell':'nm','coordinates':'nm'})

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

        # Close the output trajectory.
        self._trajectory.close()
                        
        super(ASEConverter,self).finalize()

    def parse_first_step(self):

        self._input = iread(self.configuration["trajectory_file"]["value"], index=0)
        
        for i in self._input[:1]:
            frame = i
        
        g = Graph()

        element_count = {}
        element_list = frame.get_chemical_symbols()
        id_list = np.arange(len(element_list)) + 1

        self._nAtoms = len(element_list)

        self._chemicalSystem = ChemicalSystem()


        for atnum, element in enumerate(element_list):
            if element in element_count.keys():
                element_count[element] += 1
            else:
                element_count[element] = 1
            g.add_node(atnum, element= element, atomName = f"{element}_{atnum+1}")

        for cluster in g.build_connected_components():
            if len(cluster) == 1:
                node = cluster.pop()
                try:
                    obj = Atom(node.element, name=node.atomName)
                except TypeError:
                    print("EXCEPTION in LAMMPS loader")
                    print(f"node.element = {node.element}")
                    print(f"node.atomName = {node.atomName}")
                    print(f"rankToName = {self._rankToName}")
                obj.index = node.name
            else:
                atList = []
                for atom in cluster:
                    at = Atom(symbol=atom.element, name=atom.atomName)
                    atList.append(at) 
                c = collections.Counter([at.element for at in cluster])
                name = "".join(["{:s}{:d}".format(k,v) for k,v in sorted(c.items())])
                obj = AtomCluster(name, atList)
                
            self._chemicalSystem.add_chemical_entity(obj)

REGISTRY['ase'] = ASEConverter
            
class ASEInteractiveConverter(InteractiveConverter, regkey = "ase"):
    """
    Converts any trajectory to a HDF trajectory using the ASE io module.
    """
                  
    label = "ASE"

    input_files = collections.OrderedDict()
    settings = collections.OrderedDict()
    output_files = collections.OrderedDict()

    input_files['trajectory_file'] = ('input_file', {'label':"Any MD trajectory file",
                                                  'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.lammps')})
    input_files['configuration_file'] = ('input_file', {'label':"An optional structure/configuration file",
                                                  'default':os.path.join('..','..','..','Data','Trajectories','LAMMPS','glycyl_L_alanine_charmm.lammps')})
    
    settings['time_step'] = ('float', {'label':"time step (fs)", 'default':1.0, 'mini':1.0e-9})      
    settings['time_unit'] = ('single_choice', {'label':"time step unit", 'choices':['fs','ps','ns'], 'default':'fs'})    
    settings['n_steps'] = ('integer', {'label':"number of time steps (0 for automatic detection)", 'default':0, 'mini':0})
    
    output_files['output_file'] = ('single_output_file', {'format':"hdf",'root':'config_file'})
    
    def initialize(self):
        '''
        Initialize the job.
        '''
                
        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self.parse_first_step()

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration['output_file']['file'],
            self._chemicalSystem,
            self.numberOfSteps)

        self._nameToIndex = dict([(at.name,at.index) for at in self._trajectory.chemical_system.atom_list()])

        self._start = 0

        float(self.configuration['time_step']['value'])*measure(1.0,self.configuration['time_unit']['value'])

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        self._input = iread(self.configuration["trajectory_file"]["value"])

        for stepnum, frame in enumerate(self._input):
            time = stepnum * self._timestep

        for _ in range(self._itemsPosition["TIMESTEP"][0]):
            line = self._lammps.readline()
            if not line:
                return index, None

        time = float(self._lammps.readline())*self.configuration['time_step']['value']*measure(1.0,'fs').toval('ps')

        for _ in range(self._itemsPosition["TIMESTEP"][1], self._itemsPosition["BOX BOUNDS"][0]):
            self._lammps.readline()

        unitCell = np.zeros((9), dtype=np.float64)
        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            xlo, xhi = temp
            xy = 0.0
        elif len(temp) == 3:
            xlo, xhi, xy = temp
        else:
            raise ASETrajectoryFileError("Bad format for A vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            ylo, yhi = temp
            xz = 0.0
        elif len(temp) == 3:
            ylo, yhi, xz = temp
        else:
            raise ASETrajectoryFileError("Bad format for B vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            zlo, zhi = temp
            yz = 0.0
        elif len(temp) == 3:
            zlo, zhi, yz = temp
        else:
            raise ASETrajectoryFileError("Bad format for C vector components")
                      
        # The ax component.                                      
        unitCell[0] = xhi - xlo
        
        # The bx and by components.                                      
        unitCell[3] = xy
        unitCell[4] = yhi - ylo
        
        # The cx, cy and cz components.                                      
        unitCell[6] = xz
        unitCell[7] = yz
        unitCell[8] = zhi - zlo

        unitCell = np.reshape(unitCell,(3,3))

        unitCell *= measure(1.0,'ang').toval('nm')
        unitCell = UnitCell(unitCell)

        for _ in range(self._itemsPosition["BOX BOUNDS"][1], self._itemsPosition["ATOMS"][0]):
            self._lammps.readline()

        coords = np.empty((self._trajectory.chemical_system.number_of_atoms(),3),dtype=np.float)

        for i,_ in enumerate(range(self._itemsPosition["ATOMS"][0], self._itemsPosition["ATOMS"][1])):
            temp = self._lammps.readline().split()
            idx = self._nameToIndex[self._rankToName[int(temp[0])-1]]
            coords[idx,:] = np.array([temp[self._x],temp[self._y],temp[self._z]],dtype=np.float)

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system,
                coords,
                unitCell)
            realConf = conf.to_real_configuration()
        else:
            coords *= measure(1.0,'ang').toval('nm')
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system,
                coords,
                unitCell
            )
            
        if self.configuration['fold']['value']:
            # The whole configuration is folded in to the simulation box.
            realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(time,units={'time':'ps','unit_cell':'nm','coordinates':'nm'})

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

        # Close the output trajectory.
        self._trajectory.close()
                        
        super(ASEConverter,self).finalize()

    def parse_first_step(self):

        self._input = iread(self.configuration["trajectory_file"]["value"], index=0)
        
        for i in self._input[:1]:
            frame = i
        
        g = Graph()

        element_count = {}
        element_list = frame.get_chemical_symbols()
        id_list = np.arange(len(element_list)) + 1

        self._nAtoms = len(element_list)

        self._chemicalSystem = ChemicalSystem()


        for atnum, element in enumerate(element_list):
            if element in element_count.keys():
                element_count[element] += 1
            else:
                element_count[element] = 1
            g.add_node(atnum, element= element, atomName = f"{element}_{atnum+1}")

        for cluster in g.build_connected_components():
            if len(cluster) == 1:
                node = cluster.pop()
                try:
                    obj = Atom(node.element, name=node.atomName)
                except TypeError:
                    print("EXCEPTION in LAMMPS loader")
                    print(f"node.element = {node.element}")
                    print(f"node.atomName = {node.atomName}")
                    print(f"rankToName = {self._rankToName}")
                obj.index = node.name
            else:
                atList = []
                for atom in cluster:
                    at = Atom(symbol=atom.element, name=atom.atomName)
                    atList.append(at) 
                c = collections.Counter([at.element for at in cluster])
                name = "".join(["{:s}{:d}".format(k,v) for k,v in sorted(c.items())])
                obj = AtomCluster(name, atList)
                
            self._chemicalSystem.add_chemical_entity(obj)