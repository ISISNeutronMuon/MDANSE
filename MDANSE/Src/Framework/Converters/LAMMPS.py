# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/LAMMPS.py
# @brief     Implements module/class/test LAMMPS
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import re

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class LAMMPSConfigFileError(Error):
    pass


class LAMMPSTrajectoryFileError(Error):
    pass


class LAMMPSConfigFile(dict):
    def __init__(self, filename, tolerance, smart_association):
        self._filename = filename

        self._tolerance = tolerance

        self["n_bonds"] = None

        self["bonds"] = []

        self["n_atoms"] = None

        self["n_atom_types"] = None

        self["elements"] = {}

        unit = open(self._filename, "r")
        lines = []
        for l in unit.readlines():
            l = l.strip()
            if l:
                lines.append(l)
        unit.close()

        for i, line in enumerate(lines):
            if self["n_atoms"] is None:
                m = re.match("^\s*(\d+)\s*atoms\s*$", line, re.I)
                if m:
                    self["n_atoms"] = int(m.groups()[0])

            if self["n_atom_types"] is None:
                m = re.match("^\s*(\d+)\s*atom types\s*$", line, re.I)
                if m:
                    self["n_atom_types"] = int(m.groups()[0])

            if self["n_bonds"] is None:
                m = re.match("^\s*(\d+)\s*bonds\s*$", line, re.I)
                if m:
                    self["n_bonds"] = int(m.groups()[0])

            if re.match("^\s*masses\s*$", line, re.I):
                if self["n_atom_types"] is None:
                    raise LAMMPSConfigFileError(
                        "Did not find the number of atom types."
                    )

                for j in range(1, self["n_atom_types"] + 1):
                    data_line = (
                        lines[i + j].strip().split("#")[0]
                    )  # Remove commentary if any
                    idx, mass = data_line.split()[0:2]
                    idx = int(idx)
                    mass = float(mass)
                    el = ATOMS_DATABASE.match_numeric_property(
                        "atomic_weight", mass, tolerance=self._tolerance
                    )
                    nElements = len(el)
                    if nElements == 0:
                        # No element is matching
                        raise LAMMPSConfigFileError(
                            "The atom %d with defined mass %f could not be assigned with a tolerance of %f. Please modify the mass in the config file to comply with MDANSE internal database"
                            % (idx, mass, self._tolerance)
                        )
                    elif nElements == 1:
                        # One element is matching => continue
                        self["elements"][idx] = el[0]
                    elif (
                        nElements == 2
                        and el[0][: min((len(el[0]), len(el[1])))]
                        == el[1][: min((len(el[0]), len(el[1])))]
                    ):
                        # If two elements are matching, these can be the same appearing twice (example 'Al' and 'Al27')
                        self["elements"][idx] = el[0]
                    else:
                        # Two or more elements are matching
                        if smart_association:
                            # Take the nearest match
                            matched_element = None
                            for element in el:
                                if matched_element is None:
                                    matched_element = element
                                else:
                                    if np.abs(
                                        ATOMS_DATABASE[element]["atomic_weight"] - mass
                                    ) < np.abs(
                                        ATOMS_DATABASE[matched_element]["atomic_weight"]
                                        - mass
                                    ):
                                        matched_element = element
                            self["elements"][idx] = matched_element
                        else:
                            # More than two elements are matching => error
                            raise LAMMPSConfigFileError(
                                "The atoms %s of MDANSE database matches the mass %f with a tolerance of %f. Please modify the mass in the config file to comply with MDANSE internal database"
                                % (el, mass, self._tolerance)
                            )

            m = re.match("^\s*bonds\s*$", line, re.I)
            if m:
                for j in range(1, self["n_bonds"] + 1):
                    _, _, at1, at2 = lines[i + j].split()
                    at1 = int(at1) - 1
                    at2 = int(at2) - 1
                    self["bonds"].append([at1, at2])
                self["bonds"] = np.array(self["bonds"], dtype=np.int32)

        unit.close()


class LAMMPS(Converter):
    """
    Converts a LAMMPS trajectory to a HDF trajectory.
    """

    label = "LAMMPS"

    settings = collections.OrderedDict()
    settings["config_file"] = (
        "input_file",
        {
            "label": "LAMMPS configuration file",
            "wildcard": "Config files (*.config)|*.config|All files|*",
            "default": os.path.join(
                "..",
                "..",
                "..",
                "Data",
                "Trajectories",
                "LAMMPS",
                "glycyl_L_alanine_charmm.config",
            ),
        },
    )
    settings["trajectory_file"] = (
        "input_file",
        {
            "label": "LAMMPS trajectory file",
            "default": os.path.join(
                "..",
                "..",
                "..",
                "Data",
                "Trajectories",
                "LAMMPS",
                "glycyl_L_alanine_charmm.lammps",
            ),
        },
    )
    settings["mass_tolerance"] = (
        "float",
        {"label": "mass tolerance (uma)", "default": 1.0e-3, "mini": 1.0e-9},
    )
    settings["smart_mass_association"] = (
        "boolean",
        {"label": "smart mass association", "default": True},
    )
    settings["time_step"] = (
        "float",
        {"label": "time step (fs)", "default": 1.0, "mini": 1.0e-9},
    )
    settings["n_steps"] = (
        "integer",
        {
            "label": "number of time steps (0 for automatic detection)",
            "default": 0,
            "mini": 0,
        },
    )
    settings["fold"] = (
        "boolean",
        {"default": False, "label": "Fold coordinates in to box"},
    )
    settings["output_file"] = (
        "single_output_file",
        {
            "format": "hdf",
            "root": "config_file",
            "label": "Output trajectory file name",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._lammpsConfig = LAMMPSConfigFile(
            self.configuration["config_file"]["value"],
            self.configuration["mass_tolerance"]["value"],
            self.configuration["smart_mass_association"]["value"],
        )

        self.parse_first_step()

        # Estimate number of steps if needed
        if self.numberOfSteps == 0:
            self.numberOfSteps = 1
            for line in self._lammps:
                if line.startswith("ITEM: TIMESTEP"):
                    self.numberOfSteps += 1

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemicalSystem,
            self.numberOfSteps,
        )

        self._nameToIndex = dict(
            [(at.name, at.index) for at in self._trajectory.chemical_system.atom_list]
        )

        self._lammps.seek(0, 0)

        self._start = 0

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        for _ in range(self._itemsPosition["TIMESTEP"][0]):
            line = self._lammps.readline()
            if not line:
                return index, None

        time = (
            float(self._lammps.readline())
            * self.configuration["time_step"]["value"]
            * measure(1.0, "fs").toval("ps")
        )

        for _ in range(
            self._itemsPosition["TIMESTEP"][1], self._itemsPosition["BOX BOUNDS"][0]
        ):
            self._lammps.readline()

        unitCell = np.zeros((9), dtype=np.float64)
        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            xlo, xhi = temp
            xy = 0.0
        elif len(temp) == 3:
            xlo, xhi, xy = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for A vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            ylo, yhi = temp
            xz = 0.0
        elif len(temp) == 3:
            ylo, yhi, xz = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for B vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            zlo, zhi = temp
            yz = 0.0
        elif len(temp) == 3:
            zlo, zhi, yz = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for C vector components")

        # The ax component.
        unitCell[0] = xhi - xlo

        # The bx and by components.
        unitCell[3] = xy
        unitCell[4] = yhi - ylo

        # The cx, cy and cz components.
        unitCell[6] = xz
        unitCell[7] = yz
        unitCell[8] = zhi - zlo

        unitCell = np.reshape(unitCell, (3, 3))

        unitCell *= measure(1.0, "ang").toval("nm")
        unitCell = UnitCell(unitCell)

        for _ in range(
            self._itemsPosition["BOX BOUNDS"][1], self._itemsPosition["ATOMS"][0]
        ):
            self._lammps.readline()

        coords = np.empty(
            (self._trajectory.chemical_system.number_of_atoms, 3), dtype=np.float64
        )

        for i, _ in enumerate(
            range(self._itemsPosition["ATOMS"][0], self._itemsPosition["ATOMS"][1])
        ):
            temp = self._lammps.readline().split()
            idx = self._nameToIndex[self._rankToName[int(temp[0]) - 1]]
            coords[idx, :] = np.array(
                [temp[self._x], temp[self._y], temp[self._z]], dtype=np.float64
            )

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, coords, unitCell
            )
            realConf = conf.to_real_configuration()
        else:
            coords *= measure(1.0, "ang").toval("nm")
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, coords, unitCell
            )

        if self.configuration["fold"]["value"]:
            # The whole configuration is folded in to the simulation box.
            realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        self._start += self._last

        return index, None

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x:
        @type x: any.
        """

        pass

    def finalize(self):
        """
        Finalize the job.
        """

        self._lammps.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(LAMMPS, self).finalize()

    def parse_first_step(self):
        self._lammps = open(self.configuration["trajectory_file"]["value"], "r")

        self._itemsPosition = collections.OrderedDict()

        comp = -1

        while True:
            line = self._lammps.readline()
            comp += 1

            if not line:
                break

            if line.startswith("ITEM: TIMESTEP"):
                self._itemsPosition["TIMESTEP"] = [comp + 1, comp + 2]
                continue

            elif line.startswith("ITEM: BOX BOUNDS"):
                self._itemsPosition["BOX BOUNDS"] = [comp + 1, comp + 4]
                continue

            elif line.startswith("ITEM: ATOMS"):
                keywords = line.split()[2:]

                self._id = keywords.index("id")
                self._type = keywords.index("type")

                # Field name is <x,y,z> or cd ..<x,y,z>u if real coordinates and <x,y,z>s if fractional ones
                self._fractionalCoordinates = False
                try:
                    self._x = keywords.index("x")
                    self._y = keywords.index("y")
                    self._z = keywords.index("z")
                except ValueError:
                    try:
                        self._x = keywords.index("xu")
                        self._y = keywords.index("yu")
                        self._z = keywords.index("zu")
                    except ValueError:
                        try:
                            self._x = keywords.index("xs")
                            self._y = keywords.index("ys")
                            self._z = keywords.index("zs")
                            self._fractionalCoordinates = True
                        except ValueError:
                            raise LAMMPSTrajectoryFileError(
                                "No coordinates could be found in the trajectory"
                            )

                self._rankToName = {}

                g = Graph()
                self._itemsPosition["ATOMS"] = [comp + 1, comp + self._nAtoms + 1]
                for i in range(self._nAtoms):
                    temp = self._lammps.readline().split()
                    idx = int(temp[self._id]) - 1
                    ty = int(temp[self._type])
                    name = "{:s}_{:d}".format(self._lammpsConfig["elements"][ty], idx)
                    self._rankToName[int(temp[0]) - 1] = name
                    g.add_node(
                        idx, element=self._lammpsConfig["elements"][ty], atomName=name
                    )

                if self._lammpsConfig["n_bonds"] is not None:
                    for idx1, idx2 in self._lammpsConfig["bonds"]:
                        g.add_link(idx1, idx2)

                self._chemicalSystem = ChemicalSystem()

                for cluster in g.build_connected_components():
                    if len(cluster) == 1:
                        node = cluster.pop()
                        try:
                            obj = Atom(symbol=node.element, name=node.atomName)
                        except TypeError:
                            print("EXCEPTION in LAMMPS loader")
                            print(f"node.element = {node.element}")
                            print(f"node.atomName = {node.atomName}")
                            print(f"rankToName = {self._rankToName}")
                        obj.index = node.name
                    else:
                        atList = []
                        for atom in cluster:
                            at = Atom(symbol=atom.element, name=atom.atomName)
                            atList.append(at)
                        c = collections.Counter([at.element for at in cluster])
                        name = "".join(
                            ["{:s}{:d}".format(k, v) for k, v in sorted(c.items())]
                        )
                        obj = AtomCluster(name, atList)

                    self._chemicalSystem.add_chemical_entity(obj)
                self._last = comp + self._nAtoms + 1

                break

            elif line.startswith("ITEM: NUMBER OF ATOMS"):
                self._nAtoms = int(self._lammps.readline())
                comp += 1
                continue
