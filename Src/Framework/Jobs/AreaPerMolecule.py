# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/AreaPerMolecule.py
# @brief     Implements module/class/test AreaPerMolecule
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

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob

class AreaPerMoleculeError(Error):
    pass

class AreaPerMolecule(IJob):
    '''
    Computes the area per molecule.
    
    The area per molecule is computed by simply dividing the surface of one of the simulation box faces 
    (*ab*, *bc* or *ac*) by the number of molecules with a given name. This property should be a constant unless 
    the simulation performed was in the NPT ensemble. This analysis is relevant for oriented structures like lipid membranes.
    '''
    
    label = "Area Per Molecule"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('hdf_trajectory',{'default':os.path.join('..','..','..','Data','Trajectories','MMTK','dmpc_in_periodic_universe.nc')})
    settings['frames'] = ('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['axis'] = ('multiple_choices', {'label':'area vectors','choices':['a','b','c'],'nChoices':2,'default':['a','b']})
    settings['name'] = ('string', {'label':'molecule name','default':'DMPC'})    
    settings['output_files'] = ('output_files', {'formats':["hdf","netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the analysis (open trajectory, create output variables ...)
        """

        # This will define the number of steps of the analysis. MUST be defined for all analysis.
        self.numberOfSteps = self.configuration['frames']['number']
                        
        # Extract the indexes corresponding to the axis selection (a=0,b=1,c=2).
        self._axisIndexes = self.configuration["axis"]["indexes"]

        # The number of molecules that match the input name. Must be > 0.
        self._nMolecules = len([ce for ce in self.configuration["trajectory"]["instance"].chemical_system.chemical_entities if ce.name == self.configuration["name"]["value"]])
        if self._nMolecules == 0:
            raise AreaPerMoleculeError("No molecule matches %r name." % self.configuration["name"]["value"])

        self._outputData.add("time", "line", self.configuration['frames']['time'], units='ps')

        self._outputData.add("area_per_molecule", "line", (self.configuration['frames']['number'],), axis="time", units="1/nm2")
                                         
    def run_step(self, index):
        """
        Run a single step of the analysis

        :Parameters:
            #. index (int): the index of the step.
        :Returns:
            #. index (int): the index of the step. 
            #. area per molecule (float): the calculated area per molecule for this step 
        """

        # Get the frame index
        frame_index = self.configuration['frames']['value'][index]

        configuration = self.configuration['trajectory']['instance'].configuration(frame_index)

        if not configuration.is_periodic:
            raise AreaPerMoleculeError('The configuration must be periodic')

        # Compute the area and then the area per molecule 
        unit_cell = configuration.unit_cell
        normalVect = np.cross(
            unit_cell[self._axisIndexes[0]], 
            unit_cell[self._axisIndexes[1]])
        apm = np.sqrt(np.sum(normalVect**2))/self._nMolecules
                  
        return index, apm
    
    def combine(self, index, x):
        """
        Update the output each time a step is performed
        """
        
        self._outputData['area_per_molecule'][index] = x
                                                                               
    def finalize(self):
        """
        Finalize the analysis (close trajectory, write output data ...)
        """
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['apm'] = AreaPerMolecule
     
