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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import get_spectrum


class StructureFactorFromScatteringFunction(IJob):
    """
    Computes the structure factor from a HDF file containing an intermediate scattering function.
    """

    label = "Structure Factor From Scattering Function"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_data"]

    settings = collections.OrderedDict()
    settings["sample_inc"] = (
        "HDFInputFileConfigurator",
        {
            "label": "MDANSE Incoherent Structure Factor",
            "variables": ["time", "f(q,t)_total"],
            "default": "disf_prot.h5",
        },
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"frames": "sample_inc"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        if self.configuration["output_files"]["write_logs"]:
            log_filename = self.configuration["output_files"]["root"] + ".log"
            self.add_log_file_handler(log_filename, self.configuration["output_files"]["log_level"])

        # The number of steps is set to 1 as everything is performed in the finalize method
        self.numberOfSteps = 1

        inputFile = self.configuration["sample_inc"]["instance"]

        resolution = self.configuration["instrument_resolution"]

        self._outputData.add(
            "time", "LineOutputVariable", inputFile["time"][:], units="ps"
        )

        self._outputData.add(
            "time_window",
            "LineOutputVariable",
            resolution["time_window_positive"],
            axis="time",
            units="au",
        )

        self._outputData.add("q", "LineOutputVariable", inputFile["q"][:], units="1/nm")

        self._outputData.add(
            "omega", "LineOutputVariable", resolution["omega"], units="rad/ps"
        )

        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            resolution["omega_window"],
            axis="omega",
            units="au",
        )

        nQVectors = len(inputFile["q"][:])
        nOmegas = resolution["n_omegas"]

        for k, v in list(inputFile.items()):
            if k.startswith("f(q,t)_"):
                self._outputData.add(
                    k, "SurfaceOutputVariable", v[:], axis="q|time", units="au"
                )
                suffix = k[7:]
                self._outputData.add(
                    "s(q,f)_%s" % suffix,
                    "SurfaceOutputVariable",
                    (nQVectors, nOmegas),
                    axis="q|omega",
                    units="au",
                    main_result=True,
                    partial_result=True,
                )
                self._outputData["s(q,f)_%s" % suffix][:] = get_spectrum(
                    v[:],
                    self.configuration["instrument_resolution"]["time_window"],
                    self.configuration["instrument_resolution"]["time_step"],
                    axis=1,
                )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
        """

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

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["sample_inc"]["instance"].close()
        super().finalize()
