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
import itertools as it
from typing import List, Dict, Tuple

import numpy as np

from MDANSE.MLogging import LOG
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.MolecularDynamics.TrajectoryUtils import atom_index_to_molecule_index
from MDANSE.Mathematics.Arithmetic import weight


def distance_array_2D(
    ref_atoms: np.ndarray, other_atoms: np.ndarray, cell_array: np.ndarray
):
    """Given two input arrays of atomic positions sized
    (N,3) and (M,3), returns an (M, N) array of distances
    between the atoms.

    Parameters
    ----------
    ref_atoms : np.ndarray
        (N, 3)-shaped array of atom positions
    other_atoms : np.ndarray
        (M, 3)-shaped array of atom positions
    cell_array : np.ndarray
        direct matrix of the unit cell of the system

    Returns
    -------
    np.ndarray
        (N, M)-shaped array of distances between atoms from the two arrays
    """
    diff_frac = other_atoms.reshape((len(other_atoms), 1, 3)) - ref_atoms.reshape(
        (1, len(ref_atoms), 3)
    )
    temp = diff_frac
    temp -= np.round(temp)
    diff_real = np.matmul(temp, cell_array)
    r = np.sqrt((diff_real**2).sum(axis=2))
    return r


def van_hove_distinct(
    cell: np.ndarray,
    indices_intra: Dict[int, Tuple[List[int]]],
    symbolindex: List[int],
    intra: np.ndarray,
    total: np.ndarray,
    scaleconfig_t0: np.ndarray,
    scaleconfig_t1: np.ndarray,
    rmin: float,
    dr: float,
):
    """Calculates the distance histogram between the configurations at
    times t0 and t1. Distances are calculated using the minimum image
    convention which are all worked out using the fractional coordinates
    with the unit cell of the configuration at time t1. The function can
    be used to calculate the distinct part of the van Hove function.

    The original implementation by Miguel Angel Gonzalez (Institut Laue
    Langevin) has now been replaced by numpy functions.

    Parameters
    ----------
    cell : np.ndarray
        direct matrix of the unit cell of the system
    indices_intra : Dict[int, Tuple[List[int]]]
        array indices of the distance matrix elements for each molecule in the system
    symbolindex : List[int]
        list of int values of atom types in the system
    intra : np.ndarray
        the array accumulating the intramolecular distance counts for different atom type pairs
    total : np.ndarray
        the array accumulating all the distance counts for different atom type pairs
    scaleconfig_t0 : np.ndarray
        array of atom positions at time t0
    scaleconfig_t1 : np.ndarray
        array of atom positions at time t1
    rmin : float
        lowest distance allowed in the binning of the results
    dr : float
        size of the binning step

    Returns
    -------
    Tuple[np.ndarray]
        intra and total input arrays modified by adding new counts
    """

    nbins = intra.shape[2]
    unique_types = np.unique(symbolindex)
    type_indices = {}
    for type1 in unique_types:
        type_indices[type1] = np.where(symbolindex == type1)

    all_distances = distance_array_2D(scaleconfig_t0, scaleconfig_t1, cell.T)

    bins = ((all_distances - rmin) / dr).astype(int)

    bins[range(len(symbolindex)), range(len(symbolindex))] = -1

    for dkey, indices in indices_intra.items():
        type1, type2 = dkey
        sub_bins = bins[indices]
        bin_numbers, bin_counts = np.unique(
            sub_bins,
            return_counts=True,
        )
        for bin, counts in zip(bin_numbers, bin_counts):
            if bin < 0:
                continue
            if bin >= nbins:
                continue
            intra[type1, type2, bin] += counts

    for type1 in unique_types:
        for type2 in unique_types:
            sub_bins = bins[np.ix_(type_indices[type1][0], type_indices[type2][0])]
            bin_numbers, bin_counts = np.unique(
                sub_bins,
                return_counts=True,
            )
            for bin, counts in zip(bin_numbers, bin_counts):
                if bin < 0:
                    continue
                if bin >= nbins:
                    continue
                total[type1, type2, bin] += counts

    return intra, total


def find_index_groups(
    molindex: List[int],
    symbolindex: List[int],
):
    """Finds and returns the indices of the distance array which
    will be used for calculating the intramolecular distances.
    These indices are expected to remain fixed within a run and
    are only calculated once.

    Parameters
    ----------
    molindex : List[int]
        list containing, for each atom, the number of its corresponding molecule
    symbolindex : List[int]
        atom type given as an int number for each atom in the simulation

    Returns
    -------
    Dict[Tuple[int], Tuple[List[int]]]
        A dictionary of (atom_type1, atom_type2) : row_index_list, column_index_list values
    """
    unique_types = np.unique(symbolindex)
    intra = {}
    for s1 in unique_types:
        for s2 in unique_types:
            intra[(s1, s2)] = [], []
    valid_indices = [x for x in range(len(molindex)) if molindex[x] >= 0]
    for i in valid_indices:
        for j in valid_indices:
            if i == j:
                continue
            mol1 = molindex[i]
            mol2 = molindex[j]
            type1 = symbolindex[i]
            type2 = symbolindex[j]
            dkey = (type1, type2)
            if mol1 == mol2:
                intra[dkey][0].append(i)
                intra[dkey][1].append(j)
    return intra


class VanHoveFunctionDistinct(IJob):
    """The van Hove function is related to the intermediate scattering
    function via a Fourier transform and the dynamic structure factor
    via a double Fourier transform. The van Hove function describes the
    probability of finding a particle (j) at a distance r at time t from
    a particle (i) at a time t_0. The van Hove function can be split
    into self and distinct parts. The self part includes only the
    contributions from only the same particles (i=j) while the distinct
    part includes only the contributions between different particles
    (i≠j). This job calculates a distinct part of the van Hove function,
    spherically averaged and normalised so that G(r,t)=1 as r→∞ or t→∞
    for liquid or gaseous systems and G(r,0)=PDF(r).
    """

    label = "Van Hove Function Distinct"

    enabled = True

    category = (
        "Analysis",
        "Dynamics",
    )

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
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
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def detailed_unit_cell_error(self):
        raise ValueError(
            "This analysis job requires a unit cell (simulation box) to be defined. "
            "The box will be used for calculating density in the analysis. "
            "You can add a simulation box to the trajectory using the TrajectoryEditor job. "
            "Be careful adding the simulation box, as the wrong dimensions can render the results meaningless."
        )

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["n_frames"]
        self.n_configs = self.configuration["frames"]["n_configs"]

        self._nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        self.selectedElements = self.configuration["atom_selection"]["unique_names"]
        self.nElements = len(self.selectedElements)
        self._elementsPairs = sorted(
            it.combinations_with_replacement(self.selectedElements, 2)
        )

        self.n_mid_points = len(self.configuration["r_values"]["mid_points"])

        conf = self.configuration["trajectory"]["instance"].configuration(
            self.configuration["frames"]["first"]
        )
        try:
            cell_volume = conf.unit_cell.volume
        except Exception:
            self.detailed_unit_cell_error()
        else:
            if cell_volume < 1e-9:
                self.detailed_unit_cell_error()

        self._outputData.add(
            "r",
            "LineOutputVariable",
            self.configuration["r_values"]["mid_points"],
            units="nm",
        )
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "g(r,t)_intra_total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.numberOfSteps),
            axis="r|time",
            units="au",
        )
        self._outputData.add(
            "g(r,t)_inter_total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.numberOfSteps),
            axis="r|time",
            units="au",
        )
        self._outputData.add(
            "g(r,t)_total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.numberOfSteps),
            axis="r|time",
            units="au",
        )
        for x, y in self._elementsPairs:
            self._outputData.add(
                f"g(r,t)_intra_{x}{y}",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.numberOfSteps),
                axis="r|time",
                units="au",
            )
            self._outputData.add(
                f"g(r,t)_inter_{x}{y}",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.numberOfSteps),
                axis="r|time",
                units="au",
            )
            self._outputData.add(
                f"g(r,t)_total_{x}{y}",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.numberOfSteps),
                axis="r|time",
                units="au",
            )

        lut = atom_index_to_molecule_index(
            self.configuration["trajectory"]["instance"].chemical_system
        )
        self._indices = [
            idx
            for idxs in self.configuration["atom_selection"]["indices"]
            for idx in idxs
        ]
        self.indexToMolecule = np.array([lut[i] for i in self._indices], dtype=np.int32)
        self.indexToSymbol = np.array(
            [
                self.selectedElements.index(name)
                for name in self.configuration["atom_selection"]["names"]
            ],
            dtype=np.int32,
        )

        # usually the normalization is 4 * pi * r^2 * dr which is
        # correct for small values of dr or large values of r.
        # unlike the PDF, g(r, t) may not be zero around r=0 we will use
        # the actual shell volume instead.
        self.shell_volumes = []
        for i in range(self.n_mid_points):
            self.shell_volumes.append(
                (
                    self.configuration["r_values"]["value"][i]
                    + self.configuration["r_values"]["step"]
                )
                ** 3
                - self.configuration["r_values"]["value"][i] ** 3
            )
        self.shell_volumes = (4 / 3) * np.pi * np.array(self.shell_volumes)

        self.h_intra = np.zeros(
            (self.nElements, self.nElements, self.n_mid_points, self.numberOfSteps)
        )
        self.h_inter = np.zeros(
            (self.nElements, self.nElements, self.n_mid_points, self.numberOfSteps)
        )

        self.indices_intra = find_index_groups(self.indexToMolecule, self.indexToSymbol)

    def run_step(self, time: int) -> tuple[int, tuple[np.ndarray, np.ndarray]]:
        """Calculates the distance histogram between the configurations
        at the inputted time difference. The distance histograms are
        then used to calculate the distinct part of the van Hove function.

        Parameters
        ----------
        time : int
            The time difference.

        Returns
        -------
        tuple
            A tuple containing the time difference and a tuple of the
            inter and intramolecular distance histograms.
        """
        bins_intra = np.zeros((self.nElements, self.nElements, self.n_mid_points))
        bins_total = np.zeros((self.nElements, self.nElements, self.n_mid_points))

        # average the distance histograms at the inputted time
        # difference over a number of configuration
        for i in range(self.n_configs):
            frame_index_t0 = self.configuration["frames"]["value"][i]
            conf_t0 = self.configuration["trajectory"]["instance"].configuration(
                frame_index_t0
            )
            coords_t0 = conf_t0["coordinates"][self._indices]

            frame_index_t1 = self.configuration["frames"]["value"][i + time]
            conf_t1 = self.configuration["trajectory"]["instance"].configuration(
                frame_index_t1
            )
            coords_t1 = conf_t1["coordinates"][self._indices]
            direct_cell = conf_t1.unit_cell.transposed_direct
            inverse_cell = conf_t1.unit_cell.transposed_inverse

            scaleconfig_t0 = coords_t0 @ inverse_cell
            scaleconfig_t1 = coords_t1 @ inverse_cell

            intra = np.zeros_like(bins_intra)
            total = np.zeros_like(bins_total)

            intra, total = van_hove_distinct(
                direct_cell,
                self.indices_intra,
                self.indexToSymbol,
                intra,
                total,
                scaleconfig_t0,
                scaleconfig_t1,
                self.configuration["r_values"]["first"],
                self.configuration["r_values"]["step"],
            )

            # The van Hove function will be divided by the density,
            # we multiply my the volume here and divide by the number
            # of atoms in finalize.
            bins_intra += conf_t1.unit_cell.volume * intra
            bins_total += conf_t1.unit_cell.volume * total

        return time, (bins_intra, bins_total)

    def combine(self, time: int, x: tuple[np.ndarray, np.ndarray]):
        """Add the results into the histograms for the inputted time
        difference.

        Parameters
        ----------
        time : int
            The time difference.
        x : tuple[np.ndarray, np.ndarray]
            A tuple containing a histogram of the distances between
            configurations at the inputted time difference.
        """
        self.h_intra[..., time] += x[0]
        self.h_inter[..., time] += x[1] - x[0]

    def finalize(self):
        """Using the distance histograms calculate, normalize and save the
        distinct part of the van Hove function.
        """
        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()

        for pair in self._elementsPairs:
            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]

            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if idi == idj:
                nij = ni * (ni - 1) / 2.0
            else:
                nij = ni * nj
                self.h_intra[idi, idj] += self.h_intra[idj, idi]
                self.h_inter[idi, idj] += self.h_inter[idj, idi]

            fact = 2 * nij * self.n_configs * self.shell_volumes
            van_hove_intra = self.h_intra[idi, idj, ...] / fact[:, np.newaxis]
            van_hove_inter = self.h_inter[idi, idj, ...] / fact[:, np.newaxis]
            van_hove_total = van_hove_intra + van_hove_inter

            for i, van_h in zip(
                ["intra", "inter", "total"],
                [van_hove_intra, van_hove_inter, van_hove_total],
            ):
                self._outputData[f"g(r,t)_{i}_{''.join(pair)}"][...] = van_h

        weights = self.configuration["weights"].get_weights()
        for i in ["_intra", "_inter", ""]:
            pdf = weight(
                weights,
                self._outputData,
                nAtomsPerElement,
                2,
                f"g(r,t){i if i else '_total'}_%s%s",
            )
            self._outputData[f"g(r,t){i}_total"][...] = pdf

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )
        self.configuration["trajectory"]["instance"].close()
        super().finalize()
