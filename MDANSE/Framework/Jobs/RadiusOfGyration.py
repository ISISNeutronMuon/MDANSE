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

@author: Eric C. Pellegrini
'''

import collections

import numpy

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Analysis import radius_of_gyration

class RadiusOfGyration(IJob):
    """
    Radius Of Gyration (ROG) is a measure of the size of an object,
    a surface, or an ensemble of points. It is calculated as the Root Mean Square Distance between
    the system and a reference which, in MDANSE, is the centre of gravity of the system. 
    """ 

    type = 'rog'

    label = "Radius of Gyration"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['weights'] = ('weights',{})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):
        """
        Computes the pair distribution function for a set of atoms.
        """
        self.numberOfSteps = self.configuration['frames']['number']
        
        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
        
        self._outputData.add('rog',"line", (self.configuration['frames']['number'],),'time', units="nm")

        self._indexes = self.configuration['atom_selection']['indexes']

        self._masses = numpy.array([ELEMENTS[el[0],self.configuration["weights"]["property"]] for el in self.configuration['atom_selection']['elements']],dtype=numpy.float64)

        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. rog (float): The radius of gyration
        """                

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index] 
        
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        
        # read the particle trajectory                                              
        series = self.configuration['trajectory']['instance'].universe.configuration().array[self._indexes,:]
                        
        rog = radius_of_gyration(series, masses=self._masses, root=True)
                                                 
        return index, rog
                
                        
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """   

        self._outputData['rog'][index] = x
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   
        # Write the output variables.
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()     
  
        
