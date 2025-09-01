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
from __future__ import annotations

import collections

import numpy as np
from more_itertools import always_iterable

from MDANSE.Framework.AtomGrouping.grouping import (
    pair_labels,
)
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Framework.Jobs.VanHoveFunctionDistinct import (
    CELL_SIZE_LIMIT,
    DETAILED_CELL_MESSAGE,
    intramolecular_lookup_dict,
    van_hove_distinct,
    van_hove_distinct_all_inter,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import atom_index_to_molecule_index


class DistanceHistogram(IJob):
    """Calculates a histogram of interatomic distances.

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
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
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
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

        self._indices = np.array(self.trajectory.atom_indices, dtype=np.int32)

        if self.trajectory.chemical_system.unique_molecules():
            self.indices_intra = intramolecular_lookup_dict(
                self.trajectory.chemical_system,
            )
        else:
            self.indices_intra = None
        self.intra = self.indices_intra is not None
        self.selectedElements = sorted(self.trajectory.unique_names)
        if self.indices_intra is not None and len(self.indices_intra) > len(
            self._indices
        ):
            self.indices_intra = self.indices_intra[self._indices]

        self.indexToSymbol = np.array(
            [
                self.selectedElements.index(name)
                for name in always_iterable(
                    self.trajectory.selection_getter(self.trajectory.atom_names)
                )
            ],
            dtype=np.int32,
        )

        nElements = len(self.selectedElements)

        # The histogram of the intramolecular distances.
        if self.intra:
            self.h_intra = np.zeros(
                (
                    nElements,
                    nElements,
                    len(self.configuration["r_values"]["mid_points"]),
                ),
                dtype=np.float64,
            )
        else:
            self.h_intra = None

        # The histogram of the intermolecular distances.
        self.h_total = np.zeros(
            (nElements, nElements, len(self.configuration["r_values"]["mid_points"])),
            dtype=np.float64,
        )

        self.averageDensity = 0.0

        self._nAtomsPerElement = self.trajectory.get_natoms()
        self._concentrations = {}
        for k in list(self._nAtomsPerElement.keys()):
            self._concentrations[k] = 0.0

        self.labels = pair_labels(
            self.trajectory,
        )
        self.labels_intra = pair_labels(self.trajectory, intra=True)

    def run_step(self, index):
        """Run a single step of the analysis.

        Parameters
        ----------
        index : int
            number of the simulation frame for which to calculate the distances.

        Returns
        -------
        int
            Repeated input index.
        tuple[float, ~numpy.ndarray, ~numpy.ndarray]
            The analysis results.

        """
        # get the Frame index
        frame_index = self.configuration["frames"]["value"][index]

        conf = self.trajectory.configuration(frame_index)
        if not hasattr(conf, "unit_cell"):
            raise ValueError(DETAILED_CELL_MESSAGE)
        if conf.unit_cell.volume < CELL_SIZE_LIMIT:
            raise ValueError(DETAILED_CELL_MESSAGE)

        direct_cell = conf.unit_cell.direct
        cell_volume = conf.unit_cell.volume

        coords = conf["coordinates"][self._indices]
        frac_coords = coords @ conf.unit_cell.inverse

        if self.intra:
            hIntraTemp = np.zeros(self.h_intra.shape, dtype=np.float64)
            hTotalTemp = np.zeros(self.h_total.shape, dtype=np.float64)

            van_hove_distinct(
                direct_cell,
                self.indices_intra,
                self.indexToSymbol,
                hIntraTemp,
                hTotalTemp,
                frac_coords,
                frac_coords,
                self.configuration["r_values"]["first"],
                self.configuration["r_values"]["step"],
            )

            np.multiply(hIntraTemp, cell_volume, hIntraTemp)
            np.multiply(hTotalTemp, cell_volume, hTotalTemp)
        else:
            hTotalTemp = np.zeros(self.h_total.shape, dtype=np.float64)
            hIntraTemp = None
            van_hove_distinct_all_inter(
                direct_cell,
                self.indices_intra,
                self.indexToSymbol,
                None,
                hTotalTemp,
                frac_coords,
                frac_coords,
                self.configuration["r_values"]["first"],
                self.configuration["r_values"]["step"],
            )
            np.multiply(hTotalTemp, cell_volume, hTotalTemp)

        return index, (cell_volume, hIntraTemp, hTotalTemp)

    def combine(self, _index, x):
        """Add the results of run_step to the output arrays.

        Parameters
        ----------
        index : int
            step number, not used
        x : tuple[float, np.ndarray, np.ndarray]
            output of the run_step method

        """
        nAtoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_atoms

        self.averageDensity += nAtoms / x[0]

        # The temporary distance histograms are normalized by the volume.
        # This is done for each step because the
        # volume can vary during the MD (e.g. NPT conditions).
        # This volume is the one that intervene in the density
        # calculation.
        if self.intra:
            self.h_intra += x[1]
        self.h_total += x[2]

        for k, v in list(self._nAtomsPerElement.items()):
            self._concentrations[k] += float(v) / nAtoms
