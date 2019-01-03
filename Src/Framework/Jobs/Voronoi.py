import collections

import numpy 

from MDANSE import REGISTRY
from MDANSE.Extensions import mic_fast_calc, qhull
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import factorial

def no_exc_min(l):
    try:
        return min(l)
    except:
        return - numpy.pi
    
class Voronoi(IJob):
    """
    Computes the volume of each Voronoi cell and corresponding 'neighbourhood' statistics for 3d systems. 
    Delaunay triangulation is used for the decomposition of polytops into simplexes,
    Voronoi and Delaunay tessellation are calculated using a cython wrapping of the Qhull library (scipy wrapping used as Externals)

    Voronoi analysis is another commonly-used, complementary method for characterising the local structure of a system.	
    
    **Acknowledgement:**\n
    Gael Goret, PELLEGRINI Eric
    
    """

    label = "Voronoi"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()   
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}, 'default':(0,5,1)})
    settings['pbc'] = ('boolean', {'label':'apply periodic_boundary_condition', 'default':True})
    settings['pbc_border_size'] = ('float', {'mini':0.0, 'default':0.})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
                
    def initialize(self):

        self.numberOfSteps = self.configuration['frames']['number']

        # Will store the time.
        self._outputData.add('time',"line",self.configuration['frames']['time'],units="ps")
        
        # Will store mean volume for voronoi regions.
        self.mean_volume = numpy.zeros((self.numberOfSteps)) 
                
        self.nb_init_pts = self.configuration['trajectory']['instance'].universe.numberOfAtoms()
        
        # Will store neighbourhood histogram for voronoi regions.
        self.neighbourhood_hist = {}
        
        cell = numpy.array(self.configuration['trajectory']['instance'].universe.basisVectors()).astype(numpy.float64)
        self.cell_param = numpy.array([cell[0,0], cell[1,1], cell[2,2]], dtype = numpy.float64)
        
        self.dim = 3
    
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
        
        conf = self.configuration['trajectory']['instance'].universe.configuration().array.astype(numpy.float64)

        if self.configuration['pbc']["value"]:
            conf, _ = mic_fast_calc.mic_generator_3D(conf,self.configuration['pbc_border_size']["value"],self.cell_param)
        # Computing Voronoi Diagram ...
        Voronoi = qhull.Voronoi(conf)
        vertices_coords = Voronoi.vertices # Option qhull v p 
        
        # Extracting valid Voronoi regions ...
        points_ids = Voronoi.regions # Option qhull v FN
        valid_regions_points_ids = []
        valid_region_id = []
        region_id  = -1
        for p in Voronoi.point_region:
            region_id += 1
            l = points_ids[p]
            if no_exc_min(l)>=0:
                valid_regions_points_ids.append(l)
                valid_region_id.append(region_id)
                
        valid_regions = {}
        for i in range(len(valid_region_id)):
            vrid = valid_region_id[i]
            valid_regions[vrid]= valid_regions_points_ids[i]
        
        # Extracting ridges of the valid Voronoi regions ...
        input_sites = Voronoi.ridge_points # Option qhull v Fv (part of)
        self.max_region_id = input_sites.max()
        
        # Calculating neighbourhood ...
        neighbourhood = numpy.zeros((self.max_region_id+1), dtype = numpy.int32)
        for s in input_sites.ravel():
            neighbourhood[s] +=  1
        
        # Summing into neighbourhood histogram (for valid regions only)
        for i in range(len(neighbourhood)):
            v = neighbourhood[i]
            if i in valid_region_id:
                if not self.neighbourhood_hist.has_key(v):
                    self.neighbourhood_hist[v] = 1
                else:
                    self.neighbourhood_hist[v] += 1

        # Delaunay Tesselation of each valid voronoi region ...
        delaunay_regions_for_each_valid_voronoi_region = {}
        for vrid, ids in valid_regions.items():
            if vrid >= self.nb_init_pts:
                continue
            if len(ids) == 3:
                delaunay_regions_for_each_valid_voronoi_region[vrid] = [ids]
                continue
            lut = numpy.array(ids)
            Delaunay = qhull.Delaunay(vertices_coords[ids])
            delaunay_regions_for_each_valid_voronoi_region[vrid] = [lut[dv] for dv in Delaunay.vertices]
            
        # Volume Computation ... "    
        global_volumes = {}
        for vrid, regions in delaunay_regions_for_each_valid_voronoi_region.items():
            regions_volumes = []
            for vidx in regions:
                coords = vertices_coords[vidx]
                delta = coords[1:,:]-coords[0,:]
                vidx_volume = numpy.abs(numpy.linalg.det(delta))/factorial(self.dim)
                regions_volumes.append(vidx_volume)
            global_volumes[vrid] = sum(regions_volumes)
        
        # Mean volume of Voronoi regions  
        mean =  numpy.array(global_volumes.values()).mean()
        self.mean_volume[index] = mean
        
        return index, None
    
    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x: the output of run_step method.
        @type x: no specific type.
        """
        pass
           
    def finalize(self):
        """
        Finalize the job.
        """
        max_nb_neighbour = max(self.neighbourhood_hist.keys())
        self.neighbourhood = numpy.zeros((max_nb_neighbour+1), dtype=numpy.int32)
        for k, v in self.neighbourhood_hist.items():
            self.neighbourhood[k] = v 
            
        self._outputData.add('mean_volume',"line", self.mean_volume, units="nm3") 
        
        self._outputData.add('neighbourhood_histogram',"line", self.neighbourhood, units="au") 
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
REGISTRY['vo'] = Voronoi
        
