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

@author: Eric C. Pellegrini
'''

import collections

from MMTK.Collections import Collection
from MMTK.ParticleProperties import Configuration
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center

class RefoldedMembraneTrajectory(IJob):
    """
    Rebuild the trajectory of a membrane such as the lipid compising the upper leaflet are actually on the up side of the simulation
    box and conversely the lipids that composes the lower leaflet are actually on the down side of the leaflet.
    The normal to the membrane is assumed to be parallel to z axis. 
    """
    
    type = 'rmt'
    
    label = "Refolded Membrane Trajectory"

    category = ('Macromolecules','Lipids')
    
    ancestor = "mmtk_trajectory"

    configurators = collections.OrderedDict()
    configurators['trajectory'] = ('mmtk_trajectory',{})
    configurators['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    configurators['axis'] = ('single_choice', {'label':"membrane axis", 'choices':['a','b','c'], 'default':'c'})
    configurators['upper_leaflet'] = ('string', {'label':"name of the lipid of the upper leaflet", 'default':"dmpcu"})
    configurators['lower_leaflet'] = ('string', {'label':"name of the lipid of the lower leaflet", 'default':"dmpcl"})
    configurators['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
        
        self._universe = self.configuration['trajectory']['instance'].universe

        self._upperLeaflet = Collection([obj for obj in self._universe.objectList() if obj.name == self.configuration["upper_leaflet"]["value"]])
        self._lowerLeaflet = Collection([obj for obj in self._universe.objectList() if obj.name == self.configuration["lower_leaflet"]["value"]])
        self._membrane = Collection(self._upperLeaflet,self._lowerLeaflet)

        self._upperLeafletIndexes = [at.index for at in self._upperLeaflet.atomList()]
        self._lowerLeafletIndexes = [at.index for at in self._lowerLeaflet.atomList()]
        self._membraneIndexes = [at.index for at in self._membrane.atomList()]
                        
        # The output trajectory is opened for writing.
        self._rmt = Trajectory(self._membrane, self.configuration['output_files']['files'][0], "w")
        
        # The title for the trajectory is set. 
        self._rmt.title = self.__class__.__name__

        # Create the snapshot generator.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._rmt, "all", 0, None, 1)])

        self._axis = self.configuration["axis"]["index"]                

    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. None
        """

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]
              
        # The configuration corresponding to this index is set to the universe.
        self._universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)

        conf = self._universe.contiguousObjectConfiguration()

        boxCoords = self._universe._realToBoxPointArray(conf.array)

        # Compute the center of gravity of the whole lower leaflet.
        lowerLeafletCenter = center(boxCoords[self._lowerLeafletIndexes,:])[self._axis]
        for lip in self._upperLeaflet:
            idxs = [at.index for at in lip.atomList()]
            currCenter = center(boxCoords[idxs,:])[self._axis]
            if currCenter < lowerLeafletCenter:
                boxCoords[idxs,2] += 1.0 

        upperLeafletCenter = center(boxCoords[self._upperLeafletIndexes,:])[self._axis]
        for lip in self._lowerLeaflet:
            idxs = [at.index for at in lip.atomList()]
            currCenter = center(boxCoords[idxs,:])[self._axis]
            if currCenter > upperLeafletCenter:
                boxCoords[idxs,2] -= 1.0

        conf = Configuration(self._universe, self._universe._boxToRealPointArray(boxCoords))
        
        self._universe.setConfiguration(conf)
                          
        # The times corresponding to the running index.
        t = self.configuration['frames']['time'][index]
        
        # A snapshot of the universe is written to the output trajectory.
        self._snapshot(data = {'time': t})
                                
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
        # The input trajectory is closed.
        self.configuration['trajectory']['instance'].close()
                                                    
        # The output trajectory is closed.
        self._rmt.close()