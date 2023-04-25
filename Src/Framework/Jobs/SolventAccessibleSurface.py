# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/SolventAccessibleSurface.py
# @brief     Implements module/class/test SolventAccessibleSurface
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.Extensions import sas_fast_calc

class SolventAccessibleSurface(IJob):
    """
    The Solvent Accessible Surface (SAS) is the surface area of a molecule that is accessible to a solvent. 
    SAS is typically calculated using the 'rolling ball' algorithm developed by Shrake & Rupley in 1973. 
    
    * Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.
    
    This algorithm uses a sphere (of solvent) of a particular radius to 'probe' the surface of the molecule.
   
    It involves constructing a mesh of points equidistant from each atom of the molecule 
    and uses the number of these points that are solvent accessible to determine the surface area. 
    The points are drawn at a water molecule's estimated radius beyond the van der Waals radius, 
    which is effectively similar to 'rolling a ball' along the surface.
    All points are checked against the surface of neighboring atoms to determine whether they are buried or accessible. 
    The number of points accessible is multiplied by the portion of surface area each point represents to calculate the SAS. 
    The choice of the 'probe radius' has an effect on the observed surface area - 
    using a smaller probe radius detects more surface details and therefore reports a larger surface. 
    A typical value is 0.14 nm, which is approximately the radius of a water molecule. 
    Another factor that affects the result is the definition of the VDW radii of the atoms in the molecule under study.     
    """

    label = "Solvent Accessible Surface"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}, 'default':(0,2,1)})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['n_sphere_points'] = ('integer', {'mini':1, 'default':1000})
    settings['probe_radius'] = ('float', {'mini':0.0, 'default':0.14})
    settings['output_files'] = ('output_files', {'formats':["hdf","netcdf","ascii"]})
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

        self._indexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]
        
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
                                conf.array[self._indexes,:],
                                numpy.array(self.configuration['atom_selection']['indexes'], dtype=numpy.int32).ravel(),
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
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['sas'] = SolventAccessibleSurface
     
