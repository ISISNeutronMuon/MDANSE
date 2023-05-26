# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/GaussianDynamicIncoherentStructureFactor.py
# @brief     Implements module/class/test GaussianDynamicIncoherentStructureFactor
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms

class GaussianDynamicIncoherentStructureFactor(IJob):
    """
    Computes the dynamic incoherent structure factor S_inc(Q,w) for a set of atoms in the Gaussian approximation.
    """
        
    label = "Gaussian Dynamic Incoherent Structure Factor"

    category = ('Analysis','Scattering',)
    
    ancestor = ['hdf_trajectory','molecular_viewer']
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('hdf_trajectory',{})
    settings['frames'] = ('frames', {'dependencies' : {'trajectory':'trajectory'}})
    settings['q_shells'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['instrument_resolution'] = ('instrument_resolution', {'dependencies':{'trajectory':'trajectory','frames' : 'frames'}})
    settings['projection'] = ('projection', {'label':'project coordinates'})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_incoherent2','dependencies':{'atom_selection':'atom_selection'}})
    settings['output_files'] = ('output_files', {'formats':['hdf','netcdf','ascii']})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['atom_selection']['selection_length']

        self._nQShells = self.configuration["q_shells"]["number"]
        
        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._nOmegas = self._instrResolution['n_omegas']
        
        self._kSquare = self.configuration["q_shells"]["value"]**2
        
        self._outputData.add("q","line",self.configuration["q_shells"]["value"], units="1/nm") 

        self._outputData.add("q2","line",self._kSquare,units="1/nm2") 

        self._outputData.add("time","line",self.configuration['frames']['duration'], units='ps')
        self._outputData.add("time_window","line",self._instrResolution["time_window"], units="au") 

        self._outputData.add("omega","line",self.configuration["instrument_resolution"]["omega"], units='rad/ps')
        self._outputData.add("omega_window","line",self._instrResolution["omega_window"], axis="omega", units="au") 

        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("f(q,t)_%s" % element,"surface", (self._nQShells,self._nFrames),axis="q|time", units="au")                                                 
            self._outputData.add("s(q,f)_%s" % element,"surface", (self._nQShells,self._nOmegas), axis="q|omega", units="nm2/ps") 

        self._outputData.add("f(q,t)_total","surface",(self._nQShells,self._nFrames), axis="q|time", units="au")                                                 
        self._outputData.add("s(q,f)_total","surface",(self._nQShells,self._nOmegas), axis="q|omega", units="nm2/ps") 
        
        self._atoms = sorted_atoms(self.configuration["trajectory"]["instance"].chemical_system.atom_list())

    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicSF (np.array): The atomic structure factor
        """

        # get atom index
        indexes = self.configuration['atom_selection']["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]
                        
        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            atoms,
            first=self.configuration['frames']['first'],
            last=self.configuration['frames']['last']+1,
            step=self.configuration['frames']['step'])
        
        series = self.configuration['projection']['projector'](series)

        atomicSF = np.zeros((self._nQShells,self._nFrames), dtype=np.float64)
                
        msd  = mean_square_displacement(series)

        for i, q2 in enumerate(self._kSquare):
            
            gaussian = np.exp(-msd*q2/6.0)

            atomicSF[i,:] += gaussian

        return index, atomicSF
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration['atom_selection']['names'][index]
        
        self._outputData['f(q,t)_%s' % element] += x
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()        
        for element, number in nAtomsPerElement.items():
            self._outputData['f(q,t)_%s' % element][:] /= number
            self._outputData['s(q,f)_%s' % element][:] = get_spectrum(self._outputData["f(q,t)_%s" % element],
                                                                      self.configuration["instrument_resolution"]["time_window"],
                                                                      self.configuration["instrument_resolution"]["time_step"],
                                                                      axis=1)
        weights = self.configuration['weights'].get_weights()
        
        self._outputData['f(q,t)_total'][:] = weight(weights,self._outputData,nAtomsPerElement,1,"f(q,t)_%s")
        
        self._outputData['s(q,f)_total'][:] = weight(weights,self._outputData,nAtomsPerElement,1,"s(q,f)_%s")
    
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['gdisf'] = GaussianDynamicIncoherentStructureFactor
