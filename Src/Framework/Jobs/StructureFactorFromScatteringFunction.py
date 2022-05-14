# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/StructureFactorFromScatteringFunction.py
# @brief     Implements module/class/test StructureFactorFromScatteringFunction
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

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import get_spectrum

class StructureFactorFromScatteringFunction(IJob):
    """
    Computes the structure factor from a NetCDF file containing an intermediate scattering function.
    """
        
    label = "Structure Factor From Scattering Function"

    category = ('Analysis','Scattering',)
    
    ancestor = ["netcdf_data"]
    
    settings = collections.OrderedDict()
    settings['netcdf_input_file'] = ('netcdf_input_file', {'variables':['time','f(q,t)_total'],
                                                           'default':os.path.join('..','..','..','Data','NetCDF','disf_prot.nc')})
    settings['instrument_resolution'] = ('instrument_resolution', {'dependencies':{'frames' : 'netcdf_input_file'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        # The number of steps is set to 1 as the job is defined as single McStas run.            
        self.numberOfSteps = 1
        
        inputFile = self.configuration['netcdf_input_file']['instance'] 
        
        resolution = self.configuration["instrument_resolution"]
        
        self._outputData.add("time","line", inputFile.variables['time'][:], units='ps')

        self._outputData.add("time_window","line", inputFile.variables['time_window'][:], axis="time", units="au") 

        self._outputData.add("q","line", inputFile.variables['q'].getValue(), units="1/nm") 

        self._outputData.add("omega","line", resolution["omega"], units='rad/ps')
        
        self._outputData.add("omega_window","line", resolution["omega_window"], axis="omega", units="au") 

        nQVectors = len(inputFile.variables['q'][:])
        nOmegas = resolution['n_omegas']

        for k, v in inputFile.variables.items():
            if k.startswith('f(q,t)_'):
                self._outputData.add(k,"surface", v[:], axis="q|time", units="au")                                                 
                suffix = k[7:]
                self._outputData.add("s(q,f)_%s" % suffix,"surface", (nQVectors,nOmegas), axis="q|omega", units="au") 
                self._outputData["s(q,f)_%s" % suffix][:] = get_spectrum(v[:],
                                                                         self.configuration["instrument_resolution"]["time_window"],
                                                                         self.configuration["instrument_resolution"]["time_step"],
                                                                         axis=1)
                        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
        """
        
        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['netcdf_input_file']['instance'].close()

REGISTRY['sffsf'] = StructureFactorFromScatteringFunction
