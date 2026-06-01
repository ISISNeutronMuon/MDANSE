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

import numpy as np

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    OutputTrajectory,
    PathParam,
    to_class,
)
from MDANSE.Framework.Parsers import TrjFile, XTDFile
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

FORCE_FACTOR = measure(1.0, "kcal_per_mole/ang", equivalent=True).toval("Da nm/ps2 mol")


class Forcite(Converter):
    """Converts a Forcite trajectory to an MDT trajectory."""

    label = "Forcite"

    xtd_file = PathParam[XTDFile](
        mode="r",
        extensions={"XTD files": "*.xtd"},
        label="Input XTD file",
        on_set=to_class(XTDFile),
    )
    trj_file = PathParam[TrjFile](
        mode="r",
        extensions={"TRJ files": "*.trj"},
        label="Input TRJ file",
        on_set=to_class(TrjFile),
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "xtd_file"},
        label="Atom mapping",
        default={},
    )
    fold = Boolean(label="Fold coordinates into box")
    output_files = OutputTrajectory()

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._chemical_system = ChemicalSystem()
        coordinates = np.vstack([atom.xyz for atom in self.xtd_file._atoms.values()])

        element_list = [
            get_element_from_mapping(self.atom_aliases, atom.element, type=atom.name)
            for atom in self.xtd_file._atoms.values()
        ]

        charges = [atom.charge for atom in self.xtd_file._atoms.values()]
        name_list = [atom.name for atom in self.xtd_file._atoms.values()]
        unique_labels = set(name_list)
        label_dict = {label: [] for label in unique_labels}
        for temp_index, atom in enumerate(self.xtd_file._atoms.values()):
            label_dict[atom.name].append(temp_index)

        self._chemical_system.initialise_atoms(element_list, name_list)
        self._chemical_system.add_bonds(self.xtd_file._bonds)
        self._chemical_system.add_labels(label_dict)
        self._chemical_system.find_clusters_from_bonds()

        if self.xtd_file.pbc:
            boxConf = PeriodicBoxConfiguration(
                self._chemical_system, coordinates, self.xtd_file.cell
            )
            real_conf = boxConf.to_real_configuration()
        else:
            coordinates *= measure(1.0, "ang").toval("nm")
            real_conf = RealConfiguration(
                self._chemical_system, coordinates, unit_cell=self.xtd_file._cell
            )

        real_conf.fold_coordinates()
        self._configuration = real_conf

        # The number of steps of the analysis.
        self.numberOfSteps = self.trj_file.n_frames - 1

        self.frames = self.trj_file.frames

        if self.trj_file.velocities_written:
            self._velocities = np.zeros(
                (self._chemical_system.number_of_atoms, 3), dtype=np.float64
            )
        else:
            self._velocities = None

        if self.trj_file.gradients_written:
            self._gradients = np.zeros(
                (self._chemical_system.number_of_atoms, 3), dtype=np.float64
            )
        else:
            self._gradients = None

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.output_files.path,
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.output_files.dtype,
            chunking_limit=self.output_files.chunk_size,
            compression=self.output_files.compression,
            initial_charges=charges,
        )

    def run_step(self, index: int) -> tuple[int, None]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            Index of the loop.

        Returns
        -------
        tuple[int, None]
        """

        frame = next(self.frames)

        # # If the universe is periodic set its shape with the current dimensions of the unit cell.
        conf = self._configuration
        conf["coordinates"][self.trj_file.movable_atoms, :] = frame["pos"]
        if conf.is_periodic:
            if self.trj_file.options.defcel:
                conf.unit_cell = frame["cell"]
            if self.fold:
                conf.fold_coordinates()

        if self._velocities is not None:
            self._velocities[self.trj_file.movable_atoms, :] = frame["vel"]
            conf["velocities"] = self._velocities

        if self._gradients is not None:
            self._gradients[self.trj_file.movable_atoms, :] = frame["force"]
            conf["gradients"] = self._gradients

        self._trajectory.dump_configuration(
            conf,
            frame["step_info"].time,
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
        """Dummy combine step.

        Parameters
        ----------
        _index : int
            Unused.
        _x : None
            Unused.
        """

    def finalize(self):
        """
        Finalize the job.
        """
        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
