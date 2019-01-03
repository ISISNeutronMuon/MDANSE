import collections

import numpy

from MMTK import Units

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Mathematics.Signal import differentiate
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory, sorted_atoms

class Temperature(IJob):
    """
    Computes the time-dependent temperature for a given trajectory.
	The temperature is determined from the kinetic energy i.e. the atomic velocities
	which are in turn calculated from the time-dependence of the atomic coordinates.
	Note that if the time step between frames saved in the trajectory is long (~ps) 
	compared to the time step in the MD simulations (~fs) the 
	velocities are averaged over many configurations and will not give accurate temperatures.
    """
    
    label = "Temperature"

    category = ('Analysis','Thermodynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
            
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['interpolation_order'] = ('interpolation_order', {'label':"velocities",
                                                               'dependencies':{'trajectory':'trajectory'},
                                                               'default':'no interpolation'})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
            
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        
        self.numberOfSteps = self.configuration['trajectory']['instance'].universe.numberOfAtoms()
        
        self._nFrames = self.configuration['frames']['number']

        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
        self._outputData.add("kinetic_energy","line", (self._nFrames,), axis="time",units='kJ_per_mole')
        self._outputData.add("temperature","line", (self._nFrames,), axis='time',units='K')
                                
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. kineticEnergy (numpy.array): The calculated kinetic energy
        """
        
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].universe)

        atom = atoms[index]

        symbol = atom.symbol
                                                                                    
        mass = ELEMENTS[symbol,'atomic_weight']
                
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       [atom],
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       variable=self.configuration['interpolation_order']["variable"])
             
        order = self.configuration["interpolation_order"]["value"]
                
        if order != "no interpolation":
            for axis in range(3):
                series[:,axis] = differentiate(series[:,axis], order=order, dt=self.configuration['frames']['time_step'])
        
        kineticEnergy = 0.5*mass*numpy.sum(series**2,1)
                                                                                                                   
        return index, kineticEnergy
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["kinetic_energy"] += x
                                    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        self._outputData['kinetic_energy'] /= (self.configuration['trajectory']['instance'].universe.numberOfAtoms()-1)
                                
        self._outputData['temperature'][:] = 2.0*self._outputData['kinetic_energy']/(3.0*Units.k_B)
                                
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     

REGISTRY['temp'] = Temperature
