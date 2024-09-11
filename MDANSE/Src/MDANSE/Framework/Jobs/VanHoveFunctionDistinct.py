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

import numpy as np

from MDANSE.Extensions import van_hove
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.TrajectoryUtils import atom_index_to_molecule_index
from MDANSE.Mathematics.Arithmetic import weight


class VanHoveFunctionDistinct(IJob):

    label = "Van Hove Function Distinct"

    enabled = True

    category = (
        "Analysis",
        "Scattering",
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
        {"dependencies": {"atom_selection": "atom_selection"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["n_frames"]

        self._nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        self.selectedElements = self.configuration["atom_selection"]["unique_names"]
        self.nElements = len(self.selectedElements)
        self._elementsPairs = sorted(
            it.combinations_with_replacement(self.selectedElements, 2)
        )

        self.n_min_points = len(self.configuration["r_values"]["mid_points"])

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
            (self.n_min_points, self.numberOfSteps),
            axis="r|time",
            units="au",
        )
        self._outputData.add(
            "g(r,t)_inter_total",
            "SurfaceOutputVariable",
            (self.n_min_points, self.numberOfSteps),
            axis="r|time",
            units="au",
        )
        self._outputData.add(
            "g(r,t)_total",
            "SurfaceOutputVariable",
            (self.n_min_points, self.numberOfSteps),
            axis="r|time",
            units="au",
        )
        for x, y in self._elementsPairs:
            self._outputData.add(
                "g(r,t)_intra_%s%s" % (x, y),
                "SurfaceOutputVariable",
                (self.n_min_points, self.numberOfSteps),
                axis="r|time",
                units="au",
            )
            self._outputData.add(
                "g(r,t)_inter_%s%s" % (x, y),
                "SurfaceOutputVariable",
                (self.n_min_points, self.numberOfSteps),
                axis="r|time",
                units="au",
            )
            self._outputData.add(
                "g(r,t)_total_%s%s" % (x, y),
                "SurfaceOutputVariable",
                (self.n_min_points, self.numberOfSteps),
                axis="r|time",
                units="au",
            )

        lut = atom_index_to_molecule_index(
            self.configuration["trajectory"]["instance"].chemical_system
        )
        self._indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]
        self._indexes = np.array(self._indexes, dtype=np.int32)
        self.indexToMolecule = np.array([lut[i] for i in self._indexes], dtype=np.int32)
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
        for i in range( self.n_min_points):
            self.shell_volumes.append(
                (4 / 3) * np.pi * (
                        (self.configuration["r_values"]["value"][i] +
                         self.configuration["r_values"]["step"]) ** 3
                        - self.configuration["r_values"]["value"][i] ** 3
                )
            )
        self.shell_volumes = np.array(self.shell_volumes)

        self.h_intra = np.zeros(
            (self.nElements, self.nElements, self.n_min_points, self.numberOfSteps)
        )
        self.h_inter = np.zeros(
            (self.nElements, self.nElements, self.n_min_points, self.numberOfSteps)
        )

    def run_step(self, index):
        bins_intra = np.zeros((self.nElements, self.nElements, self.n_min_points))
        bins_inter = np.zeros((self.nElements, self.nElements, self.n_min_points))

        for i in range(self.configuration["frames"]["n_configs"]):
            frame_index_t0 = self.configuration["frames"]["value"][i]
            conf_t0 = self.configuration["trajectory"]["instance"].configuration(frame_index_t0)
            coords_t0 = conf_t0["coordinates"]

            frame_index_t1 = self.configuration["frames"]["value"][i + index]
            conf_t1 = self.configuration["trajectory"]["instance"].configuration(frame_index_t1)
            coords_t1 = conf_t1["coordinates"]
            direct_cell = conf_t1.unit_cell.transposed_direct
            inverse_cell = conf_t1.unit_cell.transposed_inverse

            scaleconfig_t0 = coords_t0 @ inverse_cell
            scaleconfig_t1 = coords_t1 @ inverse_cell

            inter = np.zeros_like(bins_inter)
            intra = np.zeros_like(bins_inter)

            van_hove.van_hove(
                coords_t0,
                coords_t1,
                direct_cell,
                self._indexes,
                self.indexToMolecule,
                self.indexToSymbol,
                intra,
                inter,
                scaleconfig_t0,
                scaleconfig_t1,
                self.configuration["r_values"]["first"],
                self.configuration["r_values"]["step"],
            )

            bins_intra += conf_t1.unit_cell.volume * intra
            bins_inter += conf_t1.unit_cell.volume * inter

        return index, (bins_intra, bins_inter)

    def combine(self, index, x):
        self.h_intra[..., index] += x[0]
        self.h_inter[..., index] += x[1]

    def finalize(self):
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

            fact = nij * self.numberOfSteps * self.shell_volumes
            van_hove_intra = self.h_intra[idi, idj, ...] / fact[:, np.newaxis]
            van_hove_inter = self.h_inter[idi, idj, ...] / fact[:, np.newaxis]
            van_hove_total = van_hove_intra + van_hove_inter

            for i, van_hove in zip(
                ["intra", "inter", "total"], [van_hove_intra, van_hove_inter, van_hove_total]
            ):
                self._outputData["g(r,t)_%s_%s%s" % (i, pair[0], pair[1])][...] = van_hove

        weights = self.configuration["weights"].get_weights()
        for i in ["_intra", "_inter", ""]:
            pdf = weight(
                weights,
                self._outputData,
                nAtomsPerElement,
                2,
                "g(r,t){}_%s%s".format(i if i else "_total"),
            )
            self._outputData["g(r,t)%s_total" % i][...] = pdf

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )
        self.configuration["trajectory"]["instance"].close()
        super().finalize()
