#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
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

@author: pellegrini
'''

import collections

import numpy

from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob

class AreaPerMoleculeError(Error):
    pass

class AreaPerMolecule(IJob):
    '''
    Computes the area per molecule.
    
    The area per molecule is computed by simply dividing the surface of one of the simulation box face (ab, bc or ac) by the
    number of molecule with a given name. This property should be a constant unless the simulation performed was in NPT ensemble.
    '''
    
    type = 'apm'

    label = "Area Per Molecule"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"

    configurators = collections.OrderedDict()
    configurators['trajectory'] = ('mmtk_trajectory',{})
    configurators['frames'] = ('frames', {"dependencies":{'trajectory':'trajectory'}})
    configurators['axis'] = ('multiple_choices', {'label':'area vectors',
                                                  'choices':['a','b','c'],
                                                  'nChoices':2,
                                                  'default':['a','b']})
    configurators['name'] = ('string', {'label':'molecule name'})    
    configurators['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    configurators['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the analysis (open trajectory, create output variables ...)
        """

        # This will define the number of steps of the analysis. MUST be defined for all analysis.
        self.numberOfSteps = self.configuration['frames']['number']
                        
        # Extract the indexes corresponding to the axis selection (a=0,b=1,c=2).
        self._axisIndexes = self.configuration["axis"]["indexes"]

        # The number of molecules that match the input name. Must be > 0.
        self._nMolecules = len([obj for obj in self.configuration["trajectory"]["instance"].universe.objectList() if obj.name == self.configuration["name"]["value"]])
        if self._nMolecules == 0:
            raise AreaPerMoleculeError("No molecule matches %r name." % self.configuration["name"]["value"])

        self._outputData.add("times", "line", self.configuration['frames']['time'], units='ps')

        self._outputData.add("area_per_molecule", "line", (self.configuration['frames']['number'],), axis="times", units="1/nm2")
                                         
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
        frameIndex = self.configuration['frames']['value'][index]

        # Set the universe configuration to this frame index
        universe = self.configuration['trajectory']['instance'].universe        
        universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)

        # Compute the area and then the area per molecule 
        basisVectors = universe.basisVectors()
        normalVect = numpy.cross(basisVectors[self._axisIndexes[0]], basisVectors[self._axisIndexes[1]])
        apm = numpy.sqrt(numpy.sum(normalVect**2))/self._nMolecules
                  
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
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        self.configuration['trajectory']['instance'].close()     