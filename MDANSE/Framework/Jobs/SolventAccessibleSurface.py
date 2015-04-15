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

@author: Gael Goret, Eric C. Pellegrini
'''

import collections

import numpy

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.Extensions import sas_fast_calc

class SolventAccessibleSurface(IJob):
    """
    The Solvent Accessible Surface (SAS) is the surface area of a molecule that is accessible to a solvent. 
    SAS is typically calculated using the 'rolling ball' algorithm developed by Shrake & Rupley in 1973. 
    
    * Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.
    
    Basically This algorithm uses a sphere (of solvent) of a particular radius to 'probe' the surface of the molecule.
   
    In more detail, the algorithm consists in drawing a mesh of points equidistant from each atom of the molecule 
    and uses the number of these points that are solvent accessible to determine the surface area. 
    The points are drawn at a water molecule's estimated radius beyond the van der Waals radius, 
    which is effectively similar to 'rolling a ball' along the surface.
    All points are checked against the surface of neighboring atoms to determine whether they are buried or accessible. 
    The number of points accessible is multiplied by the portion of surface area each point represents to calculate the SAS. 
    The choice of the 'probe radius' does have an effect on the observed surface area, 
    as using a smaller probe radius detects more surface details and therefore reports a larger surface. 
    A typical value is 0.14 nm, which approximates the radius of a water molecule. 
    Another factor that affects the results is the definition of the VDW radii of the atoms in the molecule under study.     
    """

    type = 'sas'

    label = "Solvent Accessible Surface"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}, 'default':(0,2,1)})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['n_sphere_points'] = ('integer', {'mini':1, 'default':1000})
    settings['probe_radius'] = ('float', {'mini':0.0, 'default':0.14})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):

        self.numberOfSteps = self.configuration['frames']['number']

        # Will store the time.
        self._outputData.add('time',"line",self.configuration['frames']['time'],units="ps")
        
        # Will store the solvent accessible surface.                
        self._outputData.add('sas',"line",(self.configuration['frames']['number'],),axis="time",units="nm2")
        
        # Generate the sphere points that will be used to evaluate the sas per atom.
        self.spherePoints = numpy.array(generate_sphere_points(self.configuration['n_sphere_points']['value']), dtype = numpy.float64)
        # The solid angle increment used to convert the sas from a number of accessible point to a surface.
        self.solidAngleIncr = 4.0*numpy.pi/len(self.spherePoints)
        
        # A mapping between the atom indexes and covalent_radius radius for the whole universe.
        self.vdwRadii = dict([(at.index,ELEMENTS[at.symbol,'covalent_radius']) for at in self.configuration['trajectory']['instance'].universe.atomList()])
        self.vdwRadii_list = numpy.zeros( (max(self.vdwRadii.keys())+1,2), dtype = numpy.float64)
        for k,v in self.vdwRadii.items():
            self.vdwRadii_list[k] = numpy.array([k,v])[:]   
        
    def run_step(self, index):
        """
        Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.      
        """
        
        # This is the actual index of the frame corresponding to the loop index.
        frameIndex = self.configuration['frames']['value'][index]                        
        
        # The configuration corresponding to this index is set to the universe.
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        
        # The configuration is made contiguous.
        conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()
        
        # And set to the universe.
        self.configuration['trajectory']['instance'].universe.setConfiguration(conf)
        
        # Loop over the indexes of the selected atoms for the sas calculation.
        sas = sas_fast_calc.sas(index,
                                conf.array[self.configuration['atom_selection']['indexes'],:],
                                numpy.array(self.configuration['atom_selection']['groups'], dtype=numpy.int32).ravel(),
                                self.vdwRadii_list,
                                self.spherePoints,
                                self.configuration['probe_radius']['value'])
    
        return index, sas
    
    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x: the output of run_step method.
        @type x: no specific type.
        """

        # The SAS is updated with the value obtained for frame |index|.
        self._outputData['sas'][index] = x        
    
    def finalize(self):
        """
        Finalize the job.
        """
        
        # The SAS is converted from a number of accessible points to a surface.
        self._outputData['sas'] *= self.solidAngleIncr
                
        # Write the output variables.
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()     