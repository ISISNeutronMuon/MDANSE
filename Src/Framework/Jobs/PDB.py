# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/PDB.py
# @brief     Implements module/class/test PDB
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

from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.PDB import PDBFile
from MMTK.ParticleProperties import Configuration

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.Converter import Converter

class PDBConverter(Converter):
    """
    Converts a PDB trajectory to a MMTK trajectory.
    """
    
    label = "PDB"

    settings = collections.OrderedDict()  
    settings['pdb_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','PDB','2f58_nma.pdb')})
    settings['nb_frame'] = ('range', {'valueType':int, 'includeLast':True, 'mini':0.0, 'default':(0,2,1)})
    settings['time_step'] = ('float', {'mini':1.0e-6, 'default':1.0})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
     
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        # The indices of frames which should be extacted from pdb file 
        self.frame_list = self.configuration['nb_frame']["value"]
        self.numberOfSteps = self.configuration['nb_frame']["number"]

        # Create all objects from the PDB file.  
        pdb_config = PDBFile(self.configuration['pdb_file']['filename'], model=0)

        # Create the universe.
        self._universe = pdb_config.createUnitCellUniverse()
                
        # Construct system
        self._universe.addObject(pdb_config.createAll(None, 1))
        
        # Open the new trajectory 
        self._trajectory = Trajectory(self._universe, self.configuration['output_files']['files'][0], "w", "Converted from PDB")
        
        # Make a snapshot generator for saving.
        self._snapshot = SnapshotGenerator(self._universe,actions = [TrajectoryOutput(self._trajectory, None, 0, None, 1)])
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
        """
    
        frame = self.frame_list[index]
        
        pdb_config = PDBFile(self.configuration['pdb_file']['filename'], model=frame)
        uni = pdb_config.createUnitCellUniverse()
        uni.addObject(pdb_config.createAll(None, 1))
                
        univ_config  = Configuration(self._universe, uni.configuration().array)
        
        self._universe.setConfiguration(univ_config)
        self._universe.foldCoordinatesIntoBox()
        self._snapshot(data = {'time':frame})

        return index, None
    
    def combine(self, index, x):
        """
        Not used here
        """   
        pass
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 
        # Close the output trajectory.
        self._trajectory.close()

        super(PDBConverter,self).finalize()

REGISTRY['pdb'] = PDBConverter
