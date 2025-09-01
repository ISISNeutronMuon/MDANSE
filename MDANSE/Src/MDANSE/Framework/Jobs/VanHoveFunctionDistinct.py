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
import itertools as it
from collections.abc import Iterator

import numpy as np
import numpy.typing as npt
from more_itertools import always_iterable

from MDANSE.Chemistry import ChemicalSystem
from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
    pair_labels,
    update_pair_results,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum

CELL_SIZE_LIMIT = 1e-9
DETAILED_CELL_MESSAGE = (
    "This analysis job requires a unit cell (simulation box) to be defined. "
    "The box will be used for calculating density in the analysis. "
    "You can add a simulation box to the trajectory using the TrajectoryEditor job. "
    "Be careful adding the simulation box, as the wrong dimensions can render"
    "the results meaningless."
)


def distance_array_2D(
    ref_atoms: npt.NDArray[float],
    other_atoms: npt.NDArray[float],
    cell_array: npt.NDArray[float],
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
    cell: npt.NDArray[float],
    indices_intra: npt.NDArray[int],
    symbolindex: list[int],
    intra: npt.NDArray[float],
    total: npt.NDArray[float],
    coords_t0: npt.NDArray[float],
    coords_t1: npt.NDArray[float],
    rmin: float,
    dr: float,
    size_limit: int = 1024,
):
    """Return the histogram of interatomic distances.

    Calculates the distance histogram between the configurations at
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
    indices_intra : np.ndarray[int]
        array indices of the distance matrix elements for each molecule in the system
    symbolindex : list[int]
        list of int values of atom types in the system
    intra : np.ndarray
        the array of distance counts between atoms in the same molecule
    total : np.ndarray
        the array of distance counts between atoms in different molecules
    coords_t0 : np.ndarray
        array of atom positions at time t0
    coords_t1 : np.ndarray
        array of atom positions at time t1
    rmin : float
        lowest distance allowed in the binning of the results
    dr : float
        size of the binning step
    size_limit : int
        array size over which the calculation will be split into segments

    Returns
    -------
    Tuple[np.ndarray]
        intra and total input arrays modified by adding new counts

    """
    nbins = intra.shape[2]
    unique_types = np.unique(symbolindex)

    limits_t0 = range(0, len(coords_t0), size_limit)
    limits_t1 = range(0, len(coords_t1), size_limit)
    for nlim_t0, lim_t0 in enumerate(limits_t0):
        try:
            endlimit = limits_t0[nlim_t0 + 1]
        except IndexError:
            reference = coords_t0[lim_t0:]
            ref_indices = np.arange(lim_t0, len(coords_t0), dtype=int)
        else:
            reference = coords_t0[lim_t0:endlimit]
            ref_indices = np.arange(lim_t0, endlimit, dtype=int)
        for nlim_t1, lim_t1 in enumerate(limits_t1):
            try:
                endlimit_t1 = limits_t1[nlim_t1 + 1]
            except IndexError:
                subset_coords = coords_t1[lim_t1:]
                sub_indices = np.arange(lim_t1, len(coords_t1), dtype=int)
            else:
                subset_coords = coords_t1[lim_t1:endlimit_t1]
                sub_indices = np.arange(lim_t1, endlimit_t1, dtype=int)
            type_indices_ref, type_indices_sub = {}, {}
            for type1 in unique_types:
                type_indices_ref[type1] = np.where(symbolindex[ref_indices] == type1)[0]
                type_indices_sub[type1] = np.where(symbolindex[sub_indices] == type1)[0]
            mols_ref = indices_intra[ref_indices]
            mols_sub = indices_intra[sub_indices]
            intra_mask = mols_ref.reshape((1, len(mols_ref))) == mols_sub.reshape(
                (len(mols_sub), 1)
            )
            distance_array = distance_array_2D(reference, subset_coords, cell)
            bin_values = ((distance_array - rmin) / dr).astype(int)
            if ref_indices[0] == sub_indices[0]:
                diag_len = min(len(ref_indices), len(sub_indices))
                bin_values[range(diag_len), range(diag_len)] = -1
            for type_ref in unique_types:
                for type_sub in unique_types:
                    bins_subset = bin_values[
                        np.ix_(type_indices_sub[type_sub], type_indices_ref[type_ref])
                    ]
                    bin_numbers, bin_counts = np.unique(bins_subset, return_counts=True)
                    for bin, counts in zip(bin_numbers, bin_counts):
                        if bin < 0:
                            continue
                        elif bin >= nbins:
                            continue
                        else:
                            total[type_sub, type_ref, bin] += counts
            bin_values[np.where(np.logical_not(intra_mask))] = -1
            for type_ref in unique_types:
                for type_sub in unique_types:
                    bins_subset = bin_values[
                        np.ix_(type_indices_sub[type_sub], type_indices_ref[type_ref])
                    ]
                    bin_numbers, bin_counts = np.unique(bins_subset, return_counts=True)
                    for bin, counts in zip(bin_numbers, bin_counts):
                        if bin < 0:
                            continue
                        elif bin >= nbins:
                            continue
                        else:
                            intra[type_sub, type_ref, bin] += counts

    return intra, total


def van_hove_distinct_all_inter(
    cell: npt.NDArray[float],
    _indices_intra: None,
    symbolindex: list[int],
    intra: None,
    total: npt.NDArray[float],
    coords_t0: npt.NDArray[float],
    coords_t1: npt.NDArray[float],
    rmin: float,
    dr: float,
    size_limit: int = 1024,
) -> tuple[None, npt.NDArray[float]]:
    """Return the histogram of interatomic distances.

    Calculates the distance histogram between the configurations at
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
    indices_intra : None
        added for compatibility but omitted in the calculations
    symbolindex : List[int]
        list of int values of atom types in the system
    intra : None
        added for compatibility but omitted in the calculations
    total : np.ndarray
        the array of distance counts between atoms in different molecules
    coords_t0 : np.ndarray
        array of atom positions at time t0
    coords_t1 : np.ndarray
        array of atom positions at time t1
    rmin : float
        lowest distance allowed in the binning of the results
    dr : float
        size of the binning step
    size_limit : int
        array size over which the calculation will be split into segments

    Returns
    -------
    Tuple[None, np.ndarray]
        intra and total input arrays modified by adding new counts

    """
    nbins = total.shape[2]
    unique_types = np.unique(symbolindex)

    limits_t0 = range(0, len(coords_t0), size_limit)
    limits_t1 = range(0, len(coords_t1), size_limit)
    for nlim_t0, lim_t0 in enumerate(limits_t0):
        try:
            endlimit = limits_t0[nlim_t0 + 1]
        except IndexError:
            reference = coords_t0[lim_t0:]
            ref_indices = np.arange(lim_t0, len(coords_t0), dtype=int)
        else:
            reference = coords_t0[lim_t0:endlimit]
            ref_indices = np.arange(lim_t0, endlimit, dtype=int)
        for nlim_t1, lim_t1 in enumerate(limits_t1):
            try:
                endlimit_t1 = limits_t1[nlim_t1 + 1]
            except IndexError:
                subset_coords = coords_t1[lim_t1:]
                sub_indices = np.arange(lim_t1, len(coords_t1), dtype=int)
            else:
                subset_coords = coords_t1[lim_t1:endlimit_t1]
                sub_indices = np.arange(lim_t1, endlimit_t1, dtype=int)
            type_indices_ref, type_indices_sub = {}, {}
            for type1 in unique_types:
                type_indices_ref[type1] = np.where(symbolindex[ref_indices] == type1)[0]
                type_indices_sub[type1] = np.where(symbolindex[sub_indices] == type1)[0]
            distance_array = distance_array_2D(reference, subset_coords, cell)
            bin_values = ((distance_array - rmin) / dr).astype(int)
            if ref_indices[0] == sub_indices[0]:
                diag_len = min(len(ref_indices), len(sub_indices))
                bin_values[range(diag_len), range(diag_len)] = -1
            for type_ref in unique_types:
                for type_sub in unique_types:
                    bins_subset = bin_values[
                        np.ix_(type_indices_sub[type_sub], type_indices_ref[type_ref])
                    ]
                    bin_numbers, bin_counts = np.unique(bins_subset, return_counts=True)
                    for bin, counts in zip(bin_numbers, bin_counts):
                        if bin < 0:
                            continue
                        elif bin >= nbins:
                            continue
                        else:
                            total[type_sub, type_ref, bin] += counts

    return intra, total


def intramolecular_lookup_dict(
    chemical_system: ChemicalSystem.ChemicalSystem,
) -> npt.NDArray[int]:
    """Build a lookup dictionary of atom indices in the same molecule.

    Two atoms belonging to the same molecule will return the same value
    in the dictionary. Atoms not belonging to any molecule will return
    a negative value.

    Parameters
    ----------
    chemical_system : ChemicalSystem
        Chemical system of a trajectory

    Returns
    -------
    dict[int, int]
        for each atom index, the index of the corresponding molecule

    """
    result = -1 * np.arange(chemical_system.number_of_atoms, dtype=int)
    mol_index = 1
    for molecule in chemical_system._clusters:
        for mol_indices in chemical_system._clusters[molecule]:
            for index in mol_indices:
                result[index] = mol_index
            mol_index += 1
    return result


class VanHoveFunctionDistinct(IJob):
    """Calculates the distinct van Hove function.

    The van Hove function is related to the intermediate scattering
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
        """Get the input parameters from the job input parsers."""
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["n_frames"]
        self.n_configs = self.configuration["frames"]["n_configs"]
        if self.configuration["trajectory"][
            "instance"
        ].chemical_system.unique_molecules():
            self.indices_intra = intramolecular_lookup_dict(
                self.trajectory.chemical_system,
            )
        else:
            self.indices_intra = None
        self.intra = self.indices_intra is not None

        self.selectedElements = list(self.trajectory.unique_names)
        self.nElements = len(self.selectedElements)
        self._elementsPairs = sorted(
            it.combinations_with_replacement(self.selectedElements, 2),
        )
        self.labels = pair_labels(
            self.trajectory,
        )
        self.labels_intra = pair_labels(self.trajectory, intra=True)

        self.n_mid_points = len(self.configuration["r_values"]["mid_points"])

        conf = self.trajectory.configuration(
            self.configuration["frames"]["first"],
        )
        if not hasattr(conf, "unit_cell"):
            raise ValueError(DETAILED_CELL_MESSAGE)
        if conf.unit_cell.volume < CELL_SIZE_LIMIT:
            raise ValueError(DETAILED_CELL_MESSAGE)

        self._outputData.add(
            "vh/axes/r",
            "LineOutputVariable",
            self.configuration["r_values"]["mid_points"],
            units="nm",
        )
        self._outputData.add(
            "vh/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        for label, _ in self.labels:
            self._outputData.add(
                f"vh/g(r,t)/{label}",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.numberOfSteps),
                axis="vh/axes/r|vh/axes/time",
                units="au",
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "vh/g(r,t)/total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.numberOfSteps),
            axis="vh/axes/r|vh/axes/time",
            units="au",
            main_result=True,
        )
        if self.intra:
            for label, _ in self.labels_intra:
                self._outputData.add(
                    f"vh/g(r,t)/intra/{label}",
                    "SurfaceOutputVariable",
                    (self.n_mid_points, self.numberOfSteps),
                    axis="vh/axes/r|vh/axes/time",
                    units="au",
                )
            for label, _ in self.labels:
                self._outputData.add(
                    f"vh/g(r,t)/inter/{label}",
                    "SurfaceOutputVariable",
                    (self.n_mid_points, self.numberOfSteps),
                    axis="vh/axes/r|vh/axes/time",
                    units="au",
                )
            self._outputData.add(
                "vh/g(r,t)/intra/total",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.numberOfSteps),
                axis="vh/axes/r|vh/axes/time",
                units="au",
            )
            self._outputData.add(
                "vh/g(r,t)/inter/total",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.numberOfSteps),
                axis="vh/axes/r|vh/axes/time",
                units="au",
            )

        self._indices = self.trajectory.atom_indices
        self.indexToSymbol = np.array(
            [
                self.selectedElements.index(name)
                for name in always_iterable(
                    self.trajectory.selection_getter(self.trajectory.atom_names)
                )
            ],
            dtype=np.int32,
        )
        if self.indices_intra is not None and len(self.indices_intra) > len(
            self._indices
        ):
            self.indices_intra = self.indices_intra[self._indices]

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
                - self.configuration["r_values"]["value"][i] ** 3,
            )
        self.shell_volumes = (4 / 3) * np.pi * np.array(self.shell_volumes)

        self.h_intra = np.zeros(
            (self.nElements, self.nElements, self.n_mid_points, self.numberOfSteps),
        )
        self.h_total = np.zeros(
            (self.nElements, self.nElements, self.n_mid_points, self.numberOfSteps),
        )

    def run_step(
        self, time: int
    ) -> tuple[int, tuple[npt.NDArray[float], npt.NDArray[float]]]:
        """Calculate results for a single time step.

        Calculates the distance histogram between the configurations
        at the input time difference. The distance histograms are
        then used to calculate the distinct part of the van Hove function.

        Parameters
        ----------
        time : int
            The time difference.

        Returns
        -------
        tuple[int, tuple[np.ndarray]]
            A tuple containing the time difference and a tuple of the
            total and intramolecular distance histograms.
        """
        bins_intra = np.zeros((self.nElements, self.nElements, self.n_mid_points))
        bins_total = np.zeros((self.nElements, self.nElements, self.n_mid_points))

        # average the distance histograms at the input time
        # difference over a number of configuration
        for i in range(self.n_configs):
            frame_index_t0 = self.configuration["frames"]["value"][i]
            conf_t0 = self.trajectory.configuration(
                frame_index_t0,
            )
            coords_t0 = conf_t0.coordinates[self._indices]

            frame_index_t1 = self.configuration["frames"]["value"][i + time]
            conf_t1 = self.trajectory.configuration(
                frame_index_t1,
            )
            coords_t1 = conf_t1.coordinates[self._indices]
            direct_cell = conf_t1.unit_cell.direct
            inverse_cell0 = conf_t0.unit_cell.inverse
            inverse_cell1 = conf_t1.unit_cell.inverse
            frac_coords_t0 = coords_t0 @ inverse_cell0
            frac_coords_t1 = coords_t1 @ inverse_cell1
            intra = np.zeros_like(bins_intra)
            total = np.zeros_like(bins_total)

            if self.intra:
                intra, total = van_hove_distinct(
                    direct_cell,
                    self.indices_intra,
                    self.indexToSymbol,
                    intra,
                    total,
                    frac_coords_t0,
                    frac_coords_t1,
                    self.configuration["r_values"]["first"],
                    self.configuration["r_values"]["step"],
                )
                bins_intra += conf_t1.unit_cell.volume * intra
                bins_total += conf_t1.unit_cell.volume * total
            else:
                intra, total = van_hove_distinct_all_inter(
                    direct_cell,
                    self.indices_intra,
                    self.indexToSymbol,
                    intra,
                    total,
                    frac_coords_t0,
                    frac_coords_t1,
                    self.configuration["r_values"]["first"],
                    self.configuration["r_values"]["step"],
                )
                bins_total += conf_t1.unit_cell.volume * total

            # The van Hove function will be divided by the density,
            # we multiply my the volume here and divide by the number
            # of atoms in finalize.

        return time, (bins_intra, bins_total)

    def combine(
        self, time: int, x: tuple[npt.NDArray[float], npt.NDArray[float]]
    ) -> None:
        """Add the results into the histograms for the input time difference.

        Parameters
        ----------
        time : int
            The time difference.
        x : tuple[np.ndarray, np.ndarray]
            A tuple containing a histogram of the distances between
            configurations at the input time difference.

        """
        if self.intra:
            self.h_intra[..., time] += x[0]
            self.h_total[..., time] += x[1]
        else:
            self.h_total[..., time] += x[1]

    def finalize(self):
        """Apply the scaling to the summed up results.

        Using the distance histograms calculate, normalize and save the
        distinct part of the van Hove function.
        """

        def calc_func(
            label_i: str, label_j: str
        ) -> Iterator[tuple[str, bool, npt.NDArray]]:
            """Calculates the distinct part of the van Hove function
            for a given pair of element labels.

            Parameters
            ----------
            label_i : str
                The element label.
            label_j : str
                The element label.

            Yields
            ------
            name : str
                The results name.
            inter : bool
                Whether results are for intermolecular atom pairs.
            results : npt.NDArray
                The results.
            """
            n_atms = self.trajectory.get_natoms()
            ni = n_atms[label_i]
            nj = n_atms[label_j]

            idi = self.selectedElements.index(label_i)
            idj = self.selectedElements.index(label_j)

            if label_i == label_j:
                nij = ni**2 / 2.0
            else:
                nij = ni * nj
                if self.indices_intra is not None:
                    self.h_intra[idi, idj] += self.h_intra[idj, idi]
                self.h_total[idi, idj] += self.h_total[idj, idi]

            fact = 2 * nij * self.n_configs * self.shell_volumes

            van_hove_total = self.h_total[idi, idj, ...] / fact[:, np.newaxis]
            yield "vh/g(r,t)", False, van_hove_total

            if self.intra:
                van_hove_intra = self.h_intra[idi, idj, ...] / fact[:, np.newaxis]
                van_hove_inter = van_hove_total - van_hove_intra
                yield "vh/g(r,t)/inter", False, van_hove_inter
                yield "vh/g(r,t)/intra", True, van_hove_intra

        update_pair_results(self.trajectory, calc_func, self._outputData)

        nAtomsPerElement = self.trajectory.get_natoms()

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            2,
        )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = (n_selected / n_total) ** 2

        if self.intra:
            for i in ["/intra", "/inter", ""]:
                if i == "/intra":
                    labels = self.labels_intra
                else:
                    labels = self.labels
                assign_weights(
                    self._outputData, weight_dict, f"vh/g(r,t){i}/%s", labels
                )
                vhs = weighted_sum(self._outputData, f"vh/g(r,t){i}/%s", labels)
                self._outputData[f"vh/g(r,t){i}/total"][...] = vhs / fact
                self._outputData[f"vh/g(r,t){i}/total"].scaling_factor = fact
                add_grouped_totals(
                    self.trajectory,
                    self._outputData,
                    f"vh/g(r,t){i}",
                    "SurfaceOutputVariable",
                    dim=2,
                    intra=i == "/intra",
                    axis="vh/axes/r|vh/axes/time",
                    units="au",
                    main_result=i == "",
                    partial_result=i == "",
                )
        else:
            assign_weights(self._outputData, weight_dict, "vh/g(r,t)/%s", self.labels)
            vhs = weighted_sum(self._outputData, "vh/g(r,t)/%s", self.labels)
            self._outputData["vh/g(r,t)/total"][...] = vhs / fact
            self._outputData["vh/g(r,t)/total"].scaling_factor = fact

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )
        self.trajectory.close()
        super().finalize()
