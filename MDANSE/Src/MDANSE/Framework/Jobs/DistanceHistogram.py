# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DistanceHistogram.py
# @brief     Implements module/class/test DistanceHistogram
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import itertools

import numpy as np

from MDANSE.Core.Error import Error
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
        "RangeConfigurator",
        {
            "label": "r values (nm)",
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
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

        if not conf.is_periodic:
            raise Error(
                "Pair distribution function cannot be calculated for infinite universe trajectories"
            )

        direct_cell = conf.unit_cell.transposed_direct
        inverse_cell = conf.unit_cell.transposed_inverse

        cell_volume = conf.unit_cell.volume

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
