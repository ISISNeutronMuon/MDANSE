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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import get_spectrum

class StructureFactorFromScatteringFunction(IJob):
    """
    Computes the structure factor from a NetCDF file containing an intermediate scattering function.
    """
    
    type = 'sffsf'
    
    label = "Structure Factor From Scattering Function"

    category = ('Analysis','Scattering',)
    
    ancestor = ["netcdf_data","mmtk_trajectory","molecular_viewer"]
    
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
        
        self._outputData.add("time","line", inputFile.variables['time'].getValue(), units='ps')

        self._outputData.add("time_window","line", inputFile.variables['time_window'].getValue(), axis="time", units="au") 

        self._outputData.add("q","line", inputFile.variables['q'].getValue(), units="inv_nm") 

        self._outputData.add("frequency","line", resolution["frequencies"], units='THz')
        
        self._outputData.add("frequency_window","line", resolution["frequency_window"], axis="frequency", units="au") 

        nQVectors = len(inputFile.variables['q'].getValue())
        nFrequencies = resolution['n_frequencies']

        for k, v in inputFile.variables.items():
            if k.startswith('f(q,t)_'):
                self._outputData.add(k,"surface", v.getValue(), axis="q|time", units="au")                                                 
                suffix = k[7:]
                self._outputData.add("s(q,f)_%s" % suffix,"surface", (nQVectors,nFrequencies), axis="q|frequency", units="au") 
                self._outputData["s(q,f)_%s" % suffix][:] = get_spectrum(v.getValue(),
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
