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

import math
from collections import defaultdict

import MDAnalysis as mda
from more_itertools import first, first_true

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    Float,
    ManyPath,
    OutputTrajectory,
    PathParam,
    SingleChoice,
    to_class,
)
from MDANSE.Framework.Parsers import MDAnalysisTopology
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

    coordinate_format = SingleChoice(
        choices=mda._READERS.keys() | {None},
        aliases={"AUTO": None},
        default=None,
    )
    coordinate_files = ManyPath[MDAnalysisTopology](
        mode="r",
        label="Coordinate file",
        default="",
    )
    continuous = Boolean(label="Continuous frame stitching", default=False)
    topology_format = SingleChoice(
        choices=mda._PARSERS.keys() | {None},
        aliases={"AUTO": None},
        default=None,
    )
    topology_file = PathParam(
        mode="r",
        on_set_depends={
            "topology_format": "topology_format",
            "coordinate_format": "coordinate_format",
            "coordinate_files": "coordinate_files",
            "continuous": "continuous",
        },
        label="Topology file",
        on_set=MDAnalysisTopology,
    )
    time_step = Float(
        label="Time step (ps)",
        tooltip="If 0.0 use timestep from files.",
        default=0.0,
        minimum=0.0,
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "topology_file"},
        label="Atom mapping",
        default={},
    )
    fold = Boolean(label="Fold coordinates into box")
    output_files = OutputTrajectory()

    def initialize(self):
        """Load the trajectory using MDAnalysis and create the
        trajectory writer.
        """
        super().initialize()

        self.numberOfSteps = self.topology_file.n_frames

        self._chemical_system = ChemicalSystem()
        element_list = []
        name_list = []
        label_dict = defaultdict(list)

        for at_number, atom in enumerate(self.topology_file.atom_labels):
            kwargs = atom.kw

            main_label = kwargs.pop("atm_label")

            # label_list will be populated too
            tag = kwargs.get(
                first_true(("resname", "type", "name"), pred=kwargs.__contains__)
            )

            if tag:
                label_dict[tag].append(at_number)

            element = get_element_from_mapping(self.atom_aliases, main_label, **kwargs)

            for arg in ("name", "type", "element"):
                if arg in self.topology_file.atom_props:
                    name = getattr(self.topology_file.atoms[at_number], arg)
                    break
            else:
                name = None

            element_list.append(element)
            name_list.append(name)

        if None in name_list:
            name_list = None

        self._chemical_system.initialise_atoms(element_list, name_list)
        self._chemical_system.add_labels(label_dict)

        self.frames = self.topology_file.frames

        self._trajectory = TrajectoryWriter(
            self.output_files.path,
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.output_files.dtype,
            chunking_limit=self.output_files.chunk_size,
            compression=self.output_files.compression,
            initial_charges=getattr(self.topology_file.atoms, "charges", None),
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
        data = next(self.frames)

        if "unit_cell" in data:
            conf = PeriodicRealConfiguration(self._chemical_system, **data)
            if self.fold:
                conf.fold_coordinates()
        else:
            conf = RealConfiguration(self._chemical_system, **data)

        if math.isclose(self.time_step, 0.0):
            time = index * self.topology_file.timestep
        else:
            time = index * self.time_step

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
