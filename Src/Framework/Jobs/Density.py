# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Density.py
# @brief     Implements module/class/test Density
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MMTK import Units

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Framework.Units import measure
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

class Density(IJob):
    """
    Computes the atom and mass densities for a given trajectory. These are time dependent if the simulation box volume fluctuates.
    """
    
    label = "Density"

    category = ('Analysis','Thermodynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):

        self.numberOfSteps = self.configuration['frames']['number']

        self._nFrames = self.numberOfSteps
        
        self._symbols = sorted_atoms(self.configuration['trajectory']['instance'].universe,"symbol")

        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')

        self._outputData.add("mass_density","line", (self._nFrames,), axis='time', units='g/cm3')

        self._outputData.add("atomic_density","line", (self._nFrames,), axis='time', units='1/cm3')

        if not self.configuration['trajectory']['instance'].universe.is_periodic:
            raise JobError("Pair distribution function cannot be calculated for infinite universe trajectories")
                                
    def run_step(self, index):
        """
        Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.
        """

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]
                        
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
                
        cellVolume = self.configuration['trajectory']['instance'].universe.cellVolume()*measure(1.0,'nm3').toval('cm3')
                
        atomicDensity = self.configuration['trajectory']['instance'].universe.numberOfAtoms()/cellVolume
                
        massDensity = sum([ELEMENTS[s,'atomic_weight'] for s in self._symbols])/Units.Nav/cellVolume
                        
        return index, (atomicDensity, massDensity)
    
    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x:
        @type x: any.
        """
                                
        self._outputData["atomic_density"][index] = x[0]
        
        self._outputData["mass_density"][index] = x[1]
       
    def finalize(self):
        """
        Finalize the job.
        """        

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['den'] = Density
                                         
