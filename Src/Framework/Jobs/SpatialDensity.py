import collections
import os

import numpy

from MDANSE import REGISTRY
from MDANSE.Extensions import sd_fast_calc
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import build_cartesian_axes

class SpatialDensity(IJob):
    """The Spatial Density (SD) computes the 3D histograms of atomic coordinates of the a given set of target molecules 
    within the a basis defined on a reference molecule. 
    
    It can be seen as a generalization of the pair distribution function.
    
    Indeed, pair distribution functions (PDF) are defined as orientionally averaged distribution functions.
    Although these correlation functions reflect many key features of the short-range order in molecular systems, 
    an average spatial assembly of non-spherical particles can not be uniquely characterized from these one-dimensional functions.
    Structural models postulated for the molecular ordering in non-simple systems based only on one-dimensional PDFs will always be 
    somewhat ambiguous. SD analysis provides more information through a distribution function which spans both the radial and angular 
    coordinates of the separation vector. This can provide useful information about the local structure in a complex system such as the 
    relative orientation of neighbouring molecules in a liquid.
    """
        
    label = "Spatial Density"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory', {'default':os.path.join('..','..','..','Data','Trajectories', 'MMTK', 'protein_in_periodic_universe.nc')})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['spatial_resolution'] = ('float', {'mini':0.01, 'default':0.1})
    settings['reference_basis'] = ('atoms_list', {'dependencies':{'trajectory':'trajectory'},'nAtoms':3,'default':('C284H438N84O79S7',('O','C_beta','C_delta'))})
    settings['target_molecule'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'},'default':'atom_index 151'})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables.
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

        self.hist = numpy.zeros(self.gdim.astype(numpy.int32), dtype = numpy.float64)
                
        self.rX = numpy.linspace(minx, maxx, self.gdim[0])
        self.rY = numpy.linspace(miny, maxy, self.gdim[1])
        self.rZ = numpy.linspace(minz, maxz, self.gdim[2])

        self._targetIndexes  = [idx for idxs in self.configuration['target_molecule']['indexes'] for idx in idxs]
        
    def run_step(self, index):
        """
        Runs a single step of the job.
 
        :param index: the index of the step.
        :type index: int
        :return: a 2-tuple whose 1st element is the index of the step and 2nd element the distance histogram.
        :rtype: 2-tuple
        """
        
        # This is the actual index of the frame corresponding to the loop index.
        frameIndex = self.configuration['frames']['value'][index]                        
        
        # The configuration corresponding to this index is set to the universe.
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        
        directCell = numpy.array(self.configuration['trajectory']['instance'].universe.basisVectors()).astype(numpy.float64)
        reverseCell = numpy.array(self.configuration['trajectory']['instance'].universe.reciprocalBasisVectors()).astype(numpy.float64)

        # The configuration is made contiguous.
        conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()

        origins = numpy.zeros((self.configuration['reference_basis']['n_values'],3), dtype = numpy.float64)
        bases = numpy.zeros((self.configuration['reference_basis']['n_values'],3,3), dtype = numpy.float64)
        
        indexes = numpy.array(self._targetIndexes).astype(numpy.int32)
                
        for i, basis in enumerate(self.configuration['reference_basis']['atoms']):
            
            origin, x, y = basis
            
            bases[i,:,:] = numpy.array(build_cartesian_axes(conf.array[origin,:],conf.array[x,:],conf.array[y,:])).T
        
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
        Combines/synchronizes the output of `run_step` method.
        
        :param index: the index of the step.
        :type index: int
        :param x: the output of `run_step` method.
        :type x: any python object
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
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['sd'] = SpatialDensity
