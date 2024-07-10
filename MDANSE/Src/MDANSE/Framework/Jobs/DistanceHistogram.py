#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import collections
import itertools

import numpy as np

from MDANSE.Extensions import distance_histogram
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.TrajectoryUtils import atom_index_to_molecule_index


class DistanceHistogram(IJob):
    """
    Compute the Histogram of Distance, used by e.g. PDF, coordination number analysis
    """

    type = None

    enabled = False

    category = (
        "Analysis",
        "Structure",
    )

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["r_values"] = (
        "DistHistCutoffConfigurator",
        {
            "label": "r values (nm)",
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_transmutation"] = (
        "AtomTransmutationConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {"dependencies": {"atom_selection": "atom_selection"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        if self.configuration["output_files"]["write_logs"]:
            log_filename = self.configuration["output_files"]["root"] + ".log"
            self.add_log_file_handler(
                log_filename, self.configuration["output_files"]["log_level"]
            )

        self.numberOfSteps = self.configuration["frames"]["number"]

        self._indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]
        self._indexes = np.array(self._indexes, dtype=np.int32)

        self.selectedElements = self.configuration["atom_selection"]["unique_names"]

        self.indexToSymbol = np.array(
            [
                self.selectedElements.index(name)
                for name in self.configuration["atom_selection"]["names"]
            ],
            dtype=np.int32,
        )

        lut = atom_index_to_molecule_index(
            self.configuration["trajectory"]["instance"].chemical_system
        )

        self.indexToMolecule = np.array([lut[i] for i in self._indexes], dtype=np.int32)

        nElements = len(self.selectedElements)

        # The histogram of the intramolecular distances.
        self.hIntra = np.zeros(
            (nElements, nElements, len(self.configuration["r_values"]["mid_points"])),
            dtype=np.float64,
        )

        # The histogram of the intermolecular distances.
        self.hInter = np.zeros(
            (nElements, nElements, len(self.configuration["r_values"]["mid_points"])),
            dtype=np.float64,
        )

        self.scaleconfig = np.zeros(
            (self.configuration["atom_selection"]["selection_length"], 3),
            dtype=np.float64,
        )

        self.averageDensity = 0.0

        self._nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        self._concentrations = {}
        for k in list(self._nAtomsPerElement.keys()):
            self._concentrations[k] = 0.0

        self._elementsPairs = sorted(
            itertools.combinations_with_replacement(self.selectedElements, 2)
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. cellVolume (float): the volume of the current frame simulation box
            #. hIntraTemp (np.array): The calculated distance intra-molecular histogram
            #. hInterTemp (np.array): The calculated distance inter-molecular histogram
        """

        # get the Frame index
        frame_index = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frame_index)

        try:
            direct_cell = conf.unit_cell.transposed_direct
            inverse_cell = conf.unit_cell.transposed_inverse

            cell_volume = conf.unit_cell.volume
        except:
            direct_cell = np.eye(3)
            inverse_cell = np.eye(3)

            cell_volume = 1.0

        coords = conf["coordinates"]

        hIntraTemp = np.zeros(self.hIntra.shape, dtype=np.float64)
        hInterTemp = np.zeros(self.hInter.shape, dtype=np.float64)

        distance_histogram.distance_histogram(
            coords[self._indexes, :],
            direct_cell,
            inverse_cell,
            self._indexes,
            self.indexToMolecule,
            self.indexToSymbol,
            hIntraTemp,
            hInterTemp,
            self.scaleconfig,
            self.configuration["r_values"]["first"],
            self.configuration["r_values"]["step"],
        )

        np.multiply(hIntraTemp, cell_volume, hIntraTemp)
        np.multiply(hInterTemp, cell_volume, hInterTemp)

        return index, (cell_volume, hIntraTemp, hInterTemp)

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        nAtoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_atoms

        self.averageDensity += nAtoms / x[0]

        # The temporary distance histograms are normalized by the volume. This is done for each step because the
        # volume can variate during the MD (e.g. NPT conditions). This volume is the one that intervene in the density
        # calculation.
        self.hIntra += x[1]
        self.hInter += x[2]

        for k, v in list(self._nAtomsPerElement.items()):
            self._concentrations[k] += float(v) / nAtoms
