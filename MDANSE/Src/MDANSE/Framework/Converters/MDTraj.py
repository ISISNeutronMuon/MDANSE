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
from math import isclose

import mdtraj as md

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class MDTraj(Converter):
    """Converts a trajectory to the MDT format using MDTraj.

    MDTraj reads MD trajectories by specifying trajectory files and optionally
    a topology file. Multiple files can be used for the trajectory files so that
    trajectories will be stitched together.
    """

    category = ("Converters", "General")
    label = "MDTraj"
    settings = collections.OrderedDict()

    settings["coordinate_files"] = (
        "MDTrajTrajectoryFileConfigurator",
        {
            "wildcard": "All files (*)",
            "default": '["INPUT_FILENAME"]',
            "label": "Trajectory files",
        },
    )
    settings["topology_file"] = (
        "MDTrajTopologyFileConfigurator",
        {
            "wildcard": "All files (*)",
            "default": "",
            "label": "Topology file (optional)",
            "dependencies": {"coordinate_files": "coordinate_files"},
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
        "MDTrajTimeStepConfigurator",
        {
            "label": "Time step (ps)",
            "default": 0.0,
            "mini": 0.0,
            "dependencies": {
                "coordinate_files": "coordinate_files",
                "topology_file": "topology_file",
            },
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["discard_overlapping_frames"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Discard overlapping frames"},
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
        """Load the trajectory using MDTraj and create the
        trajectory writer.
        """
        coord_files = self.configuration["coordinate_files"]["filenames"]
        top_file = self.configuration["topology_file"]["filename"]
        if top_file:
            self.traj = md.load(
                coord_files,
                top=top_file,
                discard_overlapping_frames=self.configuration[
                    "discard_overlapping_frames"
                ]["value"],
            )
        else:
            self.traj = md.load(
                coord_files,
                discard_overlapping_frames=self.configuration[
                    "discard_overlapping_frames"
                ]["value"],
            )

        self.numberOfSteps = self.traj.n_frames
        mdtraj_to_mdanse = {}

        self._chemical_system = ChemicalSystem()
        elements, atom_names, atom_labels = [], [], {}
        for atnumber, at in enumerate(self.traj.topology.atoms):
            element = get_element_from_mapping(
                self.configuration["atom_aliases"]["value"],
                at.name,
                symbol=at.element.symbol,
                residue=at.residue.name,
                number=at.element.number,
                mass=at.element.mass,
            )
            elements.append(element)
            atom_names.append(at.name)
            mdtraj_to_mdanse[at.index] = atnumber
            if at.residue.name:
                try:
                    atom_labels[at.residue.name]
                except KeyError:
                    atom_labels[at.residue.name] = [atnumber]
                else:
                    atom_labels[at.residue.name].append(atnumber)
        self._chemical_system.initialise_atoms(elements, atom_names)
        self._chemical_system.add_labels(atom_labels)
        bonds = []
        for at1, at2 in self.traj.topology.bonds:
            bonds.append([mdtraj_to_mdanse[at1.index], mdtraj_to_mdanse[at2.index]])
        self._chemical_system.add_bonds(bonds)
        self._chemical_system.find_clusters_from_bonds()

        kwargs = {
            "positions_dtype": self.configuration["output_files"]["dtype"],
            "chunking_limit": self.configuration["output_files"]["chunk_size"],
            "compression": self.configuration["output_files"]["compression"],
        }
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            **kwargs,
        )
        super().initialize()

    def run_step(self, index: int):
        """For the given frame, read the MDTraj trajectory data,
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
        if self.traj.unitcell_vectors is None:
            conf = RealConfiguration(
                self._trajectory._chemical_system,
                self.traj.xyz[index],
            )
        else:
            conf = PeriodicRealConfiguration(
                self._trajectory._chemical_system,
                self.traj.xyz[index],
                UnitCell(
                    self.traj.unitcell_vectors[index],
                ),
            )
            if self.configuration["fold"]["value"]:
                conf.fold_coordinates()

        # TODO as of 11/12/2024 MDTraj does not read velocity data
        #  there is a discussion about this on GitHub
        #  (https://github.com/mdtraj/mdtraj/issues/1824).
        #  It doesn't look like they have any plans to add this but if
        #  they change their minds then we should update our code to
        #  support this.

        if self.numberOfSteps == 1:
            time = 0
        elif isclose(float(self.configuration["time_step"]["value"]), 0.0):
            time = index * self.traj.timestep
        else:
            time = index * float(self.configuration["time_step"]["value"])

        self._trajectory.dump_configuration(
            conf,
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
            },
        )

        return index, None

    def combine(self, index, x):
        pass

    def finalize(self):
        self._trajectory.close()
        super().finalize()
