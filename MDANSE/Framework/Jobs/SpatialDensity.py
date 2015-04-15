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

@author: Bachir Aoun, Gael Goret, Eric C. Pellegrini
'''

import collections

import numpy

from MDANSE.Extensions import sd_fast_calc
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import build_cartesian_axes, center_of_mass

class SpatialDensity(IJob):
    """
    The Spatial Density (SD) can be seen as an generalization of the pair distribution function.
    Indeed, pair distribution functions are defined as orientionally averaged distribution functions.
    are in the sense that, Altough these correlation functions reflects many key features of the
    short-range order in molecular systems, it should be realized that an average spatial assembly of
    non-spherical particles can not be uniquely characterized from these one-dimensionals functions.
    So, structural models postulated for the molecular ordering in nonsimple systems based only
    on one-dimensional PDF will always be somewhat ambiguous.
    
    The goal of SD analysis is to provide greater clarity in the structual analysis of molecular systems by utilizing distribution
    function which span both the radial and angular coordinates of the separation vector. 
    This can provide useful information about the average local structure in a complex system.
     """
    
    type = 'sd'
    
    label = "Spatial Density"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory', {})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['spatial_resolution'] = ('float', {'mini':0.01, 'default':0.1})
    settings['reference_basis'] = ('basis_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['target_molecule'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        self.numberOfSteps = self.configuration['frames']['number']
        
        self.resolution = self.configuration['spatial_resolution']['value'] 
                
        # Building Histogram
        
        maxx, maxy, maxz = 0,0,0
        minx, miny, minz = 10**9,10**9,10**9
        for i in range(self.numberOfSteps):
            frameIndex = self.configuration['frames']['value'][i]
            self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
            conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()
            
            minx_loc, miny_loc, minz_loc = conf.array.min(axis=0)
            maxx_loc, maxy_loc, maxz_loc = conf.array.max(axis=0)
                         
            maxx = max(maxx_loc, maxx)
            maxy = max(maxy_loc, maxy)
            maxz = max(maxz_loc, maxz)
            
            minx = min(minx, minx_loc)
            miny = min(miny, miny_loc)
            minz = min(minz, minz_loc)
            
        dimx = maxx - minx
        dimy = maxy - miny
        dimz = maxz - minz
        
        self.min = numpy.array([minx, miny, minz], dtype = numpy.float64)*numpy.sqrt(3)
        
        # orthonomalisation in 3d can project coords out of the box, sqrt(3) prevent out of bounds
        self.gdim = numpy.ceil(numpy.sqrt(3)*numpy.array([dimx, dimy, dimz])/self.resolution)+1

        self.hist = numpy.zeros(self.gdim, dtype = numpy.float64)
        
        self.rX = numpy.linspace(minx, maxx, self.gdim[0])
        self.rY = numpy.linspace(miny, maxy, self.gdim[1])
        self.rZ = numpy.linspace(minz, maxz, self.gdim[2])
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. histogram (numpy.array): The calculated distance histogram
        """
        
        # This is the actual index of the frame corresponding to the loop index.
        frameIndex = self.configuration['frames']['value'][index]                        
        
        # The configuration corresponding to this index is set to the universe.
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        
        directCell = numpy.array(self.configuration['trajectory']['instance'].universe.basisVectors()).astype(numpy.float64)
        reverseCell = numpy.array(self.configuration['trajectory']['instance'].universe.reciprocalBasisVectors()).astype(numpy.float64)
        # The configuration is made contiguous.
        
        conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()

        origins = numpy.zeros((self.configuration['reference_basis']['n_basis'],3), dtype = numpy.float64)
        bases = numpy.zeros((self.configuration['reference_basis']['n_basis'],3,3), dtype = numpy.float64)
        
        indexes = numpy.array(self.configuration['target_molecule']['indexes']).astype(numpy.int32)
        
        for i, basis in enumerate(self.configuration['reference_basis']['basis']):
            originIndexes, xIndexes, yIndexes = basis
            origins[i,:] = center_of_mass(conf.array[originIndexes], None)
            
            x = center_of_mass(conf.array[xIndexes,:], None)
            y = center_of_mass(conf.array[yIndexes,:], None)

            bases[i,:,:] = numpy.array(build_cartesian_axes(origins[i,:],x,y)).T
        
        hist = numpy.zeros_like(self.hist, dtype=numpy.int32)
        
        hist = sd_fast_calc.spatial_density(conf.array[indexes,:],
                                            indexes,
                                            directCell,
                                            reverseCell,
                                            origins,
                                            bases,
                                            self.min,
                                            self.resolution,
                                            hist)
    
        return index, hist
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """     

        # updating histogram
        self.hist += x
        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """         
        
        self._outputData.add("x","line",self.rX,units='nm') 
        self._outputData.add("y","line",self.rY,units='nm') 
        self._outputData.add("z","line",self.rZ,units='nm') 
        self._outputData.add("inter_spatial_density","volume",self.hist)          
        
        # Write the output variables.
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()