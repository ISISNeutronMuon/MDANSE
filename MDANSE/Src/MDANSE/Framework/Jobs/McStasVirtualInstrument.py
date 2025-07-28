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
import io
import shutil
import subprocess
import tempfile
from functools import partial
from pathlib import Path

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG

MCSTAS_UNITS_LUT = {
    "rad/ps": measure(1, "rad/ps", equivalent=True).toval("meV"),
    "nm2/ps": measure(1, "nm2/ps", equivalent=True).toval("b/ps"),
    "nm2": measure(1, "nm2").toval("b"),
    "1/nm": measure(1, "1/nm").toval("1/ang"),
}

NAVOGADRO = 6.02214129e23


def _startswith(key: str, line: str) -> bool:
    return line.strip().startswith(key)


class McStasError(Error):
    pass


class McStasVirtualInstrument(IJob):
    """
    Performs a virtual neutron scattering experiment using a binding to the McStas, neutron ray-tracing code.

        This analysis requires the coherent and incoherent dynamic structure factors to have been calculated
        and an instrument to be chosen.
        The result is the instrument-dependent perturbation of the sum of the scattering contributions including
        instrument resolution, self-shielding and multiple scattering.
    """

    enabled = False

    label = "McStas Virtual Instrument"

    category = (
        "Analysis",
        "Virtual Instruments",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["sample_coh"] = (
        "HDFInputFileConfigurator",
        {
            "widget": "InputFileConfigurator",
            "label": "MDANSE Coherent Structure Factor",
            "variables": ["q", "omega", "s(q,f)_total"],
            "default": "dcsf_prot.h5",
        },
    )
    settings["sample_inc"] = (
        "HDFInputFileConfigurator",
        {
            "widget": "InputFileConfigurator",
            "label": "MDANSE Incoherent Structure Factor",
            "variables": ["q", "omega", "s(q,f)_total"],
            "default": "disf_prot.h5",
        },
    )
    settings["temperature"] = (
        "FloatConfigurator",
        {
            "default": 298.0,
            "label": "The sample temperature to be used in the simulation.",
        },
    )
    settings["display"] = (
        "BooleanConfigurator",
        {"label": "trace the 3D view of the simulation"},
    )
    settings["instrument"] = (
        "McStasInstrumentConfigurator",
        {"label": "mcstas instrument", "default": "OUTPUT_FILENAME.out"},
    )
    settings["options"] = ("McStasOptionsConfigurator", {"label": "mcstas options"})
    settings["parameters"] = (
        "McStasParametersConfigurator",
        {
            "label": "instrument parameters",
            "dependencies": {"instrument": "instrument"},
            "exclude": ["sample_coh", "sample_inc"],
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})

    @property
    def mcstas_output_dir(self) -> Path:
        """
        Output directory as path.
        """
        return Path(self.configuration["options"]["mcstas_output_directory"])

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        # The number of steps is set to 1 as the job is defined as single McStas run.
        self.numberOfSteps = 1

        symbols = self.trajectory.chemical_system.atom_list

        # Compute some parameters used for a proper McStas run
        self._mcStasPhysicalParameters = {"density": 0.0}
        self._mcStasPhysicalParameters["V_rho"] = 0.0
        self._mcStasPhysicalParameters["weight"] = sum(
            self.trajectory.get_atom_property(s, "atomic_weight") for s in symbols
        )
        self._mcStasPhysicalParameters["sigma_abs"] = (
            np.mean(
                [self.trajectory.get_atom_property(s, "xs_absorption") for s in symbols]
            )
            * MCSTAS_UNITS_LUT["nm2"]
        )
        self._mcStasPhysicalParameters["sigma_coh"] = (
            np.mean(
                [self.trajectory.get_atom_property(s, "xs_coherent") for s in symbols]
            )
            * MCSTAS_UNITS_LUT["nm2"]
        )
        self._mcStasPhysicalParameters["sigma_inc"] = (
            np.mean(
                [self.trajectory.get_atom_property(s, "xs_incoherent") for s in symbols]
            )
            * MCSTAS_UNITS_LUT["nm2"]
        )
        for frameIndex in self.configuration["frames"]["value"]:
            configuration = self.trajectory.configuration(frameIndex)
            cellVolume = configuration._unit_cell.volume
            self._mcStasPhysicalParameters["density"] += (
                self._mcStasPhysicalParameters["weight"] / cellVolume
            )
            self._mcStasPhysicalParameters["V_rho"] += (
                self.configuration["trajectory"][
                    "instance"
                ].chemical_system.number_of_atoms
                / cellVolume
            )
        self._mcStasPhysicalParameters["density"] /= self.configuration["frames"][
            "n_frames"
        ]
        self._mcStasPhysicalParameters["V_rho"] /= self.configuration["frames"][
            "n_frames"
        ]
        # The density is converty in g/cm3
        self._mcStasPhysicalParameters["density"] /= NAVOGADRO / measure(
            1.0, "cm3"
        ).toval("nm3")
        self._mcStasPhysicalParameters["V_rho"] *= measure(1.0, "1/nm3").toval("1/ang3")

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
        """

        sqw = ["sample_coh", "sample_inc"]
        sqwInput = ""
        self.outFile = {}
        for typ in sqw:
            fout = tempfile.NamedTemporaryFile(mode="w", delete=False)
            # for debugging, we use a real file here:
            # fout = open(
            #     "/Users/maciej.bartkowiak/an_example/mcstas/Persistent_file_for_"
            #     + typ
            #     + ".sqw",
            #     "w",
            # )

            fout.write("# Physical parameters:\n")
            for k, v in list(self._mcStasPhysicalParameters.items()):
                fout.write(f"# {k} {v} \n")

            fout.write(f"# Temperature {self.configuration['temperature']['value']} \n")
            fout.write("#\n")

            for var in self.configuration[typ].variables:
                fout.write(f"# {var}\n")

                data = self.configuration[typ][var][:]
                LOG.info(f"In {typ} the variable {var} has shape {data.shape}")
                LOG.info(f"Values of {var}: min={data.min()}, max = {data.max()}")
                data_unit = self.configuration[typ]._units[var]
                try:
                    data *= MCSTAS_UNITS_LUT[data_unit]
                except KeyError:
                    LOG.error(
                        f"Could not find the physical unit {data_unit} in the lookup table."
                    )

                np.savetxt(fout, np.atleast_2d(data), delimiter=" ", newline="\n")

            fout.close()
            self.outFile[typ] = fout.name
            # self.outFile[typ] = (
            #     "/Users/maciej.bartkowiak/an_example/mcstas/Persistent_file_for_"
            #     + typ
            #     + ".sqw"
            # )
            sqwInput += f"{typ}={fout.name} "

        # sys.exit(0)

        trace = ""
        if self.configuration["display"]["value"]:
            trace = " --trace "
        execPath = self.configuration["instrument"]["value"]
        options = self.configuration["options"]["value"]
        parameters = self.configuration["parameters"]["value"]

        cmdLine = [execPath]
        cmdLine.extend(options)
        cmdLine.append(sqwInput)
        cmdLine.append(trace)
        cmdLine.extend(parameters)

        LOG.info(" ".join(cmdLine))

        s = subprocess.Popen(
            " ".join(cmdLine),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        out, _ = s.communicate()

        for line in out.splitlines():
            if "ERROR" in line.decode(encoding="utf-8"):
                raise McStasError(f"An error occured during McStas run: {out}")

        out_file = self.mcstas_output_dir / "mcstas_mdanse.mvi"
        with out_file.open("w") as f:
            f.write(out.decode(encoding="utf-8"))

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

        # Rename and move to the result dir the SQW file input
        for typ, fname in self.outFile.items():
            shutil.move(fname, self.mcstas_output_dir / f"{typ}.sqw")

        # Convert McStas output files into NetCDF format
        self.convert(self.configuration["options"]["mcstas_output_directory"])

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )
        super().finalize()

    def treat_str_var(self, s):
        return s.strip().replace(" ", "_")

    def unique(self, key, d, value=None):
        skey = key
        i = 0
        if value is not None:
            for k, v in list(d.items()):
                if v.shape != value.shape:
                    continue
                if np.allclose(v, value):
                    return k
        while key in d:
            key = f"{skey}_{i:d}"
            i += 1
        return key

    def convert(self, sim_dir: Path | str):
        """
        Convert McStas data set to netCDF File Format
        """

        sim_dir = Path(sim_dir)
        typique_sim_fnames = ["mccode.sim", "mcstas.sim"]

        for sim_fname in typique_sim_fnames:
            sim_file = sim_dir / sim_fname
            if sim_file.is_file():
                break

        if not sim_file:
            raise Exception(f"Dataset {sim_file} does not exist!")

        isBegin = partial(_startswith, "begin")
        isCompFilename = partial(_startswith, "filename:")
        # First, determine if this is single or overview plot...
        SimFile = list(filter(isBegin, open(sim_file).readlines()))
        Datfile = 0
        if SimFile == []:
            FS = self.read_monitor(sim_file)
            typ = FS["type"].split("(")[0].strip()
            if typ != "multiarray_1d":
                FS = self.save_single(FS)
                raise OSError("Invalid")
                Datfile = 1

        # Get filenames from the sim file
        MonFiles = list(filter(isCompFilename, open(sim_file).readlines()))
        L = len(MonFiles)
        FSlist = []
        # Scan or overview?
        if L == 0:
            """Scan view"""
            if Datfile == 0:
                isFilename = partial(_startswith, "filename")

                Scanfile = list(filter(isFilename, open(sim_file).readlines()))
                Scanfile = Scanfile[0].split(": ")
                Scanfile = sim_dir / Scanfile[1].strip()
                # Proceed to load scan datafile
                FS = self.read_monitor(Scanfile)
                L = (len(FS["variables"].split()) - 1) / 2
                self.scan_flag = 1
                for j in range(0, L):
                    FSsingle = self.get_monitor(FS, j)
                    FSlist[len(FSlist) :] = [FSsingle]
                    FSlist[j] = self.save_single(FSsingle)
                    self.scan_length = FSsingle["data"].shape[0]
        else:
            """Overview or single monitor"""
            for j in range(0, L):
                MonFile = MonFiles[j].split(":")
                MonFile = MonFile[1].strip()
                MonFile = sim_dir / MonFile
                FS = self.read_monitor(MonFile)
                FSlist[len(FSlist) :] = [FS]
                FSlist[j] = self.save_single(FS)

    def save_single(self, FileStruct):
        """
        save a single 1D/2D data array with axis into a NetCDF file format.
          input:  FileStruct as obtained from read_monitor()
          output: FileStruct data structure
        """

        typ = FileStruct["type"].split("(")[0].strip()

        if typ == "array_1d":
            # 1D data set
            Xmin = eval(FileStruct["xlimits"].split()[0])
            Xmax = eval(FileStruct["xlimits"].split()[1])
            x = FileStruct["data"][:, 0]
            y = FileStruct["data"][:, 1]

            Title = self.unique(
                self.treat_str_var(FileStruct["component"]), self._outputData
            )
            xlabel = self.unique(
                self.treat_str_var(FileStruct["xlabel"]), self._outputData, x
            )

            self._outputData[xlabel] = IOutputVariable.create(
                "LineOutputVariable", x, xlabel, units="au"
            )
            self._outputData[Title] = IOutputVariable.create(
                "LineOutputVariable", y, Title, axis=str(xlabel), units="au"
            )

        elif typ == "array_2d":
            # 2D data set
            mysize = FileStruct["data"].shape

            data = FileStruct["data"]
            mysize = data.shape
            data = data.T

            Xmin = eval(FileStruct["xylimits"].split()[0])
            Xmax = eval(FileStruct["xylimits"].split()[1])
            Ymin = eval(FileStruct["xylimits"].split()[2])
            Ymax = eval(FileStruct["xylimits"].split()[3])

            x = np.linspace(Xmin, Xmax, mysize[1])
            y = np.linspace(Ymin, Ymax, mysize[0])

            title = self.unique(
                self.treat_str_var(FileStruct["component"]), self._outputData
            )
            xlabel = self.unique(
                self.treat_str_var(FileStruct["xlabel"]), self._outputData, x
            )
            ylabel = self.unique(
                self.treat_str_var(FileStruct["ylabel"]), self._outputData, y
            )

            self._outputData.add(xlabel, "LineOutputVariable", x, units="au")
            self._outputData.add(ylabel, "LineOutputVariable", y, units="au")
            self._outputData.add(
                title,
                "SurfaceOutputVariable",
                data,
                axis=f"{xlabel}|{ylabel}",
                units="au",
                main_result=True,
                partial_result=True,
            )

        return FileStruct

    def read_monitor(self, simFile):
        """
        Read a monitor file (McCode format).

        :param simFile: the path for the monitor file.
        :type simFile: str

        :return: a dictionary built from the evaluation of McStas monitor file header that will contains the data and metadata about the monitor.
        :rtype: dict
        """

        # Read header
        isHeader = partial(_startswith, "#")
        f = open(simFile)
        Lines = f.readlines()
        Header = list(filter(isHeader, Lines))
        f.close()

        # Traverse header and define corresponding 'struct'
        strStruct = "{"
        for j in range(0, len(Header)):
            # Field name and data
            Line = Header[j]
            Line = Line[2 : len(Line)].strip()
            Line = Line.split(":")
            Field = Line[0]
            Value = ""
            Value = "".join(":".join(Line[1 : len(Line)]).split("'"))
            strStruct = strStruct + "'" + Field + "':'" + Value + "'"
            if j < len(Header) - 1:
                strStruct += ","
        strStruct = strStruct + "}"
        Filestruct = eval(strStruct)
        # Add the data block

        data = []
        with open(simFile, encoding="utf-8") as file:
            lines = file.readlines()

        header = True
        for line in lines:
            if line.startswith("#"):
                if header:
                    continue
                else:
                    break
            else:
                if header:
                    header = False
                data.append(line)

        Filestruct["data"] = np.genfromtxt(io.StringIO(" ".join(data)))
        Filestruct["fullpath"] = simFile

        return Filestruct

    def get_monitor(self, monitor, col):
        """
        Extract one of the monitor in scan steps called from: display

        :param monitor:  the dictionary that contains data and metadata about the monitor (obtained from `read_monitor`)
        :type monitor: dict
        :param col: index of the monitor column to extract.
        :type col: int
        :return: a dictionary that contains data and metadata about monitor `j`.
        :rtype: dict
        """

        # Ugly, hard-coded...
        data = monitor["data"][:, (0, 2 * col + 1, 2 * col + 2)]
        variables = monitor["variables"].split()
        FSsingle = {
            "xlimits": monitor["xlimits"],
            "data": data,
            "component": variables[col + 1],
            "values": "",
            "type": "array_1d(100)",
            "xlabel": monitor["xlabel"],
            "ylabel": monitor["ylabel"],
            "File": "Scan",
            "title": "",
        }

        return FSsingle
