# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Gromacs.py
# @brief     Implements module/class/test Gromacs
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

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Extensions import xtc, trr
from MDANSE.Framework.Jobs.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

class GromacsConverterError(Error):
    pass

class GromacsConverter(Converter):
    """
    Converts a Gromacs trajectory to a HDF trajectory.
    """
                  
    label = "Gromacs"

    settings = collections.OrderedDict()           
    settings['pdb_file'] = ('input_file',
                            {'wildcard': 'PDB files (*.pdb)|*.pdb|All files|*',
                             'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'Gromacs', 'md.pdb')})
    settings['xtc_file'] = ('input_file',
                            {'wildcard': 'XTC files (*.xtc)|*.xtc|TRR files (*.trr)|*.trr|All files|*',
                             'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'Gromacs', 'md.xtc'),
                             'label': 'xtc or trr file'})
    settings['fold'] = ('boolean', {'default': False, 'label': 'Fold coordinates in to box'})
    settings['output_file'] = ('single_output_file', {'format': 'hdf', 'root': 'pdb_file'})

    def initialize(self):
        '''
        Initialize the job.
        '''
        data_to_be_written = ["configuration", "time"]

        # Create XTC or TRR object depending on which kind of trajectory was loaded
        if self.configuration["xtc_file"]["filename"][-4:] == '.xtc':
            self._xdr_file = xtc.XTCTrajectoryFile(self.configuration["xtc_file"]["filename"], "r")
            self._xtc = True
        elif self.configuration["xtc_file"]["filename"][-4:] == '.trr':
            self._xdr_file = trr.TRRTrajectoryFile(self.configuration["xtc_file"]["filename"], "r")
            self._xtc = False

            # Extract information about whether velocities and forces are present in the TRR file
            try:
                self._read_velocities = self._xdr_file.has_velocities
                self._read_forces = self._xdr_file.has_forces
            except AttributeError:
                self._read_velocities, self._read_forces = self._xdr_file._check_has_velocities_forces()
                if self._read_velocities < 0 or self._read_forces < 0:
                    raise RuntimeError("Could not determine whether velocities or forces are present!")

            # The TRRTrajectoryFile object returns ints for these values, so turn them into bools
            self._read_velocities, self._read_forces = bool(self._read_velocities), bool(self._read_forces)

            if self._read_velocities:
                data_to_be_written.append("velocities")
            if self._read_forces:
                data_to_be_written.append("gradients")
        else:
            raise GromacsConverterError('Invalid file format: Gromacs converter can only convert XTC and TRR files, '
                                        'but %s was provided.' % self.configuration["xtc_file"]["filename"][-4:])

        # The number of steps of the analysis.
        self.numberOfSteps = len(self._xdr_file)

        # Create all chemical entities from the PDB file.  
        pdb_reader = PDBReader(self.configuration['pdb_file']['filename'])
        chemical_system = pdb_reader.build_chemical_system()

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration['output_file']['file'],
            chemical_system,
            self.numberOfSteps)

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        variables = {}

        # The x, y and z values of the current frame.
        if self._xtc:
            coords, times, steps, box = self._xdr_file.read(1)
        else:
            coords, times, steps, box, __, velocities, forces = self._xdr_file.read(1,
                                                                                    get_velocities=self._read_velocities,
                                                                                    get_forces=self._read_forces)
            if self._read_velocities:
                variables['velocities'] = velocities[0,:,:].astype(float)
            if self._read_forces:
                variables['gradients'] = forces[0,:,:].astype(float)

        conf = PeriodicRealConfiguration(
            self._trajectory.chemical_system,
            coords,
            box[0,:,:],
            **variables
        )
        
        if self.configuration['fold']["value"]:        
            conf.fold_coordinates()

        self._trajectory.chemical_system.configuration = conf

        # The current time.
        time = times[0]

        self._trajectory.dump_configuration(time)
                                        
        return index, None

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x:
        @type x: any.
        """

        pass

    def finalize(self):
        """
        Finalize the job.
        """
        
        self._xdr_file.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(GromacsConverter,self).finalize()

REGISTRY['gromacs'] = GromacsConverter
