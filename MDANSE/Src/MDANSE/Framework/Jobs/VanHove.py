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

import numpy as np

from MDANSE.Extensions import van_hove
from MDANSE.Framework.Jobs.IJob import IJob


class VanHove(IJob):

    label = "Van Hove Function"

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
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

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
            "g(r,t)",
            "SurfaceOutputVariable",
            (self.configuration["frames"]["n_frames"], len(self.configuration["r_values"]["mid_points"])),
            axis="time|r",
            units="au",
        )

        self.numberOfSteps = self.configuration["frames"]["n_frames"]

        # usually the normalization is 4 * pi * r^2 * dr which is
        # correct for small values of dr or large values of r.
        # since g(r, t) may not be zero around r=0 we will use the
        # actual shell volume instead.
        self.shell_volumes = []
        for i in range(len(self.configuration["r_values"]["mid_points"])):
            self.shell_volumes.append(
                (4 / 3) * np.pi * (
                        (self.configuration["r_values"]["value"][i] +
                         self.configuration["r_values"]["step"]) ** 3
                        - self.configuration["r_values"]["value"][i] ** 3
                )
            )
        self.shell_volumes = np.array(self.shell_volumes)

    def run_step(self, index):
        bins = np.zeros_like(self.configuration["r_values"]["mid_points"])

        for i in range(self.configuration["frames"]["n_configs"]):
            frame_index_t0 = self.configuration["frames"]["value"][i]

            conf_t0 = self.configuration["trajectory"]["instance"].configuration(frame_index_t0)
            coords_t0 = conf_t0["coordinates"]
            direct_cell = conf_t0.unit_cell.transposed_direct
            inverse_cell = conf_t0.unit_cell.transposed_inverse

            frame_index_t1 = self.configuration["frames"]["value"][i + index]
            conf_t1 = self.configuration["trajectory"]["instance"].configuration(frame_index_t1)
            coords_t1 = conf_t1["coordinates"]

            scaleconfig_t0 = np.zeros_like(coords_t0)
            scaleconfig_t1 = np.zeros_like(coords_t0)

            van_hove.van_hove(
                coords_t0,
                coords_t1,
                direct_cell,
                inverse_cell,
                bins,
                scaleconfig_t0,
                scaleconfig_t1,
                self.configuration["r_values"]["first"],
                self.configuration["r_values"]["step"],
            )

        return index, bins / self.configuration["frames"]["n_configs"]

    def combine(self, index, x):
        self._outputData["g(r,t)"][index, :] += x / self.shell_volumes

    def finalize(self):
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
