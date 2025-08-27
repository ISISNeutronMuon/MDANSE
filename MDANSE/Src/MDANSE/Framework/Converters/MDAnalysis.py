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

import MDAnalysis as mda

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class MDAnalysis(Converter):
    """Converts a trajectory to the MDT format using MDAnalysis.

    MDAnalysis reads MD trajectories by specifying
    topology and coordinate files. Multiple files can be used for the
    coordinate files so that trajectories will be stitched together.
    For supported file formats, the continuous option ensures that
    duplicated time-frames will not be added, see
    <a href="https://userguide.mdanalysis.org/stable/reading_and_writing.html">reading and writing</a>.
    For topology and coordinate files supported by MDAnalysis see
    <a href="https://userguide.mdanalysis.org/stable/formats/index.html#formats">formats</a>.
    """

    category = ("Converters", "General")
    label = "MDAnalysis"
    settings = collections.OrderedDict()
    settings["topology_file"] = (
        "MDAnalysisTopologyFileConfigurator",
        {
            "wildcard": "All files (*)",
            "default": "INPUT_FILENAME",
            "label": "Topology file",
        },
    )
    settings["coordinate_files"] = (
        "MDAnalysisCoordinateFileConfigurator",
        {
            "wildcard": "All files (*)",
            "default": "",
            "label": "Coordinate files (optional)",
            "dependencies": {"input_file": "topology_file"},
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "topology_file"},
        },
    )
    settings["time_step"] = (
        "MDAnalysisTimeStepConfigurator",
        {
            "label": "Time step (ps)",
            "default": 0.0,
            "mini": 0.0,
            "dependencies": {
                "topology_file": "topology_file",
                "coordinate_files": "coordinate_files",
            },
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["continuous"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Continuous frame stitching"},
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "label": "MDANSE trajectory (filename, format)",
            "formats": ["MDTFormat"],
            "root": "config_file",
        },
    )

    def initialize(self):
        """Load the trajectory using MDAnalysis and create the
        trajectory writer.
        """
        coord_format = self.configuration["coordinate_files"]["format"]
        coord_files = self.configuration["coordinate_files"]["filenames"]

        if len(coord_files) <= 1 or coord_format is None:
            self.u = mda.Universe(
                self.configuration["topology_file"]["filename"],
                *coord_files,
                continuous=self.configuration["continuous"]["value"],
                format=coord_format,
                topology_format=self.configuration["topology_file"]["format"],
            )
        else:
            coord_files = [(i, coord_format) for i in coord_files]
            self.u = mda.Universe(
                self.configuration["topology_file"]["filename"],
                coord_files,
                continuous=self.configuration["continuous"]["value"],
                topology_format=self.configuration["topology_file"]["format"],
            )

        self.numberOfSteps = len(self.u.trajectory)

        self._chemical_system = ChemicalSystem()
        element_list = []
        name_list = []
        label_dict = {}

        for at_number, at in enumerate(self.u.atoms):
            kwargs = {}
            for arg in ["element", "name", "type", "resname", "mass"]:
                if hasattr(at, arg):
                    kwargs[arg] = getattr(at, arg)
            # the first out of the list above will be the main label
            (k, main_label) = next(iter(kwargs.items()))
            # label_list will be populated too
            if "resname" in kwargs:
                tag = kwargs["resname"]
            elif "type" in kwargs:
                tag = kwargs["type"]
            elif "name" in kwargs:
                tag = kwargs["name"]
            else:
                tag = None
            if tag:
                if tag in label_dict.keys():
                    label_dict[tag] += [at_number]
                else:
                    label_dict[tag] = [at_number]
            kwargs.pop(k)
            element = get_element_from_mapping(
                self.configuration["atom_aliases"]["value"], main_label, **kwargs
            )

            name = None
            for arg in ["name", "type", "element"]:
                if hasattr(at, arg):
                    name = getattr(at, arg)
                    break
            element_list.append(element)
            name_list.append(name)
        if None in name_list:
            name_list = None
        self._chemical_system.initialise_atoms(element_list, name_list)
        self._chemical_system.add_labels(label_dict)

        kwargs = {
            "positions_dtype": self.configuration["output_files"]["dtype"],
            "chunking_limit": self.configuration["output_files"]["chunk_size"],
            "compression": self.configuration["output_files"]["compression"],
        }
        if hasattr(self.u.atoms, "charges"):
            kwargs["initial_charges"] = self.u.atoms.charges

        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            **kwargs,
        )
        super().initialize()

    def run_step(self, index: int):
        """For the given frame, read the MDAnalysis trajectory data,
        convert and write it out to the MDT file.

        Parameters
        ----------
        index : int
            The frame index.

        Returns
        -------
        tuple[int, None]
            A tuple of the job index and None.
        """
        self.u.trajectory[index]

        # convert from MDAnalysis units to MDANSE units
        # see https://userguide.mdanalysis.org/stable/units.html for
        # default units in MDAnalysis
        if self.u.trajectory.ts.triclinic_dimensions is None:
            conf = RealConfiguration(
                self._trajectory._chemical_system,
                self.u.trajectory.ts.positions * measure(1.0, "ang").toval("nm"),
            )
        else:
            conf = PeriodicRealConfiguration(
                self._trajectory._chemical_system,
                self.u.trajectory.ts.positions * measure(1.0, "ang").toval("nm"),
                UnitCell(
                    self.u.trajectory.ts.triclinic_dimensions
                    * measure(1.0, "ang").toval("nm")
                ),
            )

            if self.configuration["fold"]["value"]:
                conf.fold_coordinates()

            if hasattr(self.u.trajectory.ts, "velocities"):
                conf["velocities"] = self.u.trajectory.ts.velocities * measure(
                    1.0, "ang/ps"
                ).toval("nm/ps")

            if hasattr(self.u.trajectory.ts, "forces"):
                conf["gradients"] = self.u.trajectory.ts.forces * measure(
                    1.0, "kJ/mol ang", equivalent=True
                ).toval("Da nm/ps2")

        if float(self.configuration["time_step"]["value"]) == 0.0:
            time = index * self.u.trajectory.ts.dt
        else:
            time = index * float(self.configuration["time_step"]["value"])

        self._trajectory.dump_configuration(
            conf,
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
                "gradients": "Da nm/ps2",
            },
        )

        return index, None

    def combine(self, index, x):
        pass

    def finalize(self):
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()
        super().finalize()
