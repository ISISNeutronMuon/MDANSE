# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DL_POLY.py
# @brief     Implements module/class/test DL_POLY
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


from MDANSE.Chemistry import ATOMS_DATABASE, MOLECULES_DATABASE
from MDANSE.Chemistry.ChemicalEntity import (
    Atom,
    AtomCluster,
    ChemicalSystem,
    Molecule,
    is_molecule,
    translate_atom_names,
)
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell

_HISTORY_FORMAT = {}
_HISTORY_FORMAT["2"] = {
    "rec1": 81,
    "rec2": 31,
    "reci": 61,
    "recii": 37,
    "reciii": 37,
    "reciv": 37,
    "reca": 43,
    "recb": 37,
    "recc": 37,
    "recd": 37,
}
_HISTORY_FORMAT["3"] = {
    "rec1": 73,
    "rec2": 73,
    "reci": 73,
    "recii": 73,
    "reciii": 73,
    "reciv": 73,
    "reca": 73,
    "recb": 73,
    "recc": 73,
    "recd": 73,
}
_HISTORY_FORMAT["4"] = {
    "rec1": 73,
    "rec2": 73,
    "reci": 73,
    "recii": 73,
    "reciii": 73,
    "reciv": 73,
    "reca": 73,
    "recb": 73,
    "recc": 73,
    "recd": 73,
}


class FieldFileError(Error):
    pass


class HistoryFileError(Error):
    pass


class DL_POLYConverterError(Error):
    pass


class FieldFile(dict):
    def __init__(self, filename, aliases):
        self._filename = filename

        self._aliases = aliases

        self.parse()

    def parse(self):
        # The FIELD file is opened for reading, its contents stored into |lines| and then closed.
        unit = open(self._filename, "r")

        # Read and remove the empty and comments lines from the contents of the FIELD file.
        lines = [
            line.strip()
            for line in unit.readlines()
            if line.strip() and not re.match("#", line)
        ]

        # Close the FIELD file.
        unit.close()

        self["title"] = lines.pop(0)

        self["units"] = lines.pop(0)

        # Extract the number of molecular types
        _, self["n_molecular_types"] = re.match(
            "(molecules|molecular types)\s+(\d+)", lines.pop(0), re.IGNORECASE
        ).groups()

        self["n_molecular_types"] = int(self["n_molecular_types"])

        molBlocks = [
            i for i, line in enumerate(lines) if re.match("finish", line, re.IGNORECASE)
        ]

        if self["n_molecular_types"] != len(molBlocks):
            raise FieldFileError("Error in the definition of the molecular types")

        self["molecules"] = []

        first = 0

        for last in molBlocks:
            moleculeName = lines[first]

            # Extract the number of molecular types
            nMolecules = re.match(
                "nummols\s+(\d+)", lines[first + 1], re.IGNORECASE
            ).groups()[0]
            nMolecules = int(nMolecules)

            for i in range(first + 2, last):
                match = re.match("atoms\s+(\d+)", lines[i], re.IGNORECASE)
                if match:
                    nAtoms = int(match.groups()[0])

                    sumAtoms = 0

                    comp = i + 1

                    atoms = []

                    while sumAtoms < nAtoms:
                        sitnam = lines[comp][:8].strip()

                        vals = lines[comp][8:].split()

                        if sitnam in self._aliases:
                            element = self._aliases[sitnam]
                        else:
                            element = sitnam
                            while 1:
                                if element in ATOMS_DATABASE:
                                    break
                                element = element[:-1]
                                if not element:
                                    raise FieldFileError(
                                        "Could not define any element from %r" % sitnam
                                    )

                        try:
                            nrept = int(vals[2])
                        except IndexError:
                            nrept = 1

                        atoms.extend([(sitnam, element)] * nrept)

                        sumAtoms += nrept

                        comp += 1

                    self["molecules"].append([moleculeName, nMolecules, atoms])

                    break

            first = last + 1

    def build_chemical_system(self, chemicalSystem):
        chemicalEntities = []

        for db_name, nMolecules, atomic_contents in self["molecules"]:
            # Loops over the number of molecules of the current type.
            for i in range(nMolecules):
                if is_molecule(db_name):
                    mol_name = "{:s}".format(db_name)
                    mol = Molecule(db_name, mol_name)
                    renamedAtoms = translate_atom_names(
                        MOLECULES_DATABASE,
                        db_name,
                        [name for name, _ in atomic_contents],
                    )
                    mol.reorder_atoms(renamedAtoms)
                    chemicalEntities.append(mol)
                else:
                    # This list will contains the instances of the atoms of the molecule.
                    atoms = []
                    # Loops over the atom of the molecule.
                    for j, (name, element) in enumerate(atomic_contents):
                        # The atom is created.
                        a = Atom(symbol=element, name="%s_%s" % (name, j))
                        atoms.append(a)

                    if len(atoms) > 1:
                        ac = AtomCluster("{:s}".format(db_name), atoms)
                        chemicalEntities.append(ac)
                    else:
                        chemicalEntities.append(atoms[0])

        for ce in chemicalEntities:
            chemicalSystem.add_chemical_entity(ce)


class HistoryFile(dict):
    def __init__(self, filename, version="2"):
        self["instance"] = open(filename, "rb")

        testLine = self["instance"].readline()

        lenTestLine = len(testLine)

        if lenTestLine not in [73, 74, 81, 82]:
            raise HistoryFileError("Invalid DLPOLY history file")

        self["instance"].seek(0, 0)

        self["version"] = version

        offset = lenTestLine - _HISTORY_FORMAT[self["version"]]["rec1"]

        self._headerSize = (
            _HISTORY_FORMAT[self["version"]]["rec1"]
            + _HISTORY_FORMAT[self["version"]]["rec2"]
            + 2 * offset
        )

        self["instance"].read(_HISTORY_FORMAT[self["version"]]["rec1"] + offset)

        data = self["instance"].read(_HISTORY_FORMAT[self["version"]]["rec2"] + offset)

        self["keytrj"], self["imcon"], self["natms"] = [
            int(v) for v in data.split()[0:3]
        ]

        if self["keytrj"] not in list(range(3)):
            raise HistoryFileError("Invalid value for trajectory output key.")

        if self["imcon"] not in list(range(4)):
            raise HistoryFileError(
                "Invalid value for periodic boundary conditions key."
            )

        if self["imcon"] == 0:
            self._configHeaderSize = _HISTORY_FORMAT[self["version"]]["reci"]
        else:
            self._configHeaderSize = (
                _HISTORY_FORMAT[self["version"]]["reci"]
                + 3 * _HISTORY_FORMAT[self["version"]]["recii"]
                + 4 * offset
            )

        self._configSize = (
            _HISTORY_FORMAT[self["version"]]["reca"]
            + offset
            + (self["keytrj"] + 1) * (_HISTORY_FORMAT[self["version"]]["recb"] + offset)
        ) * self["natms"]

        self._frameSize = self._configHeaderSize + self._configSize

        self["instance"].seek(0, 2)

        self["n_frames"] = (
            self["instance"].tell() - self._headerSize
        ) / self._frameSize

        self["instance"].seek(self._headerSize)

        data = self["instance"].read(self._configHeaderSize).splitlines()

        line = data[0].split()

        self._firstStep = int(line[1])

        self._timeStep = float(line[5])

        self._maskStep = 3 + 3 * (self["keytrj"] + 1) + 1

        if (self["version"] == "3") or (self["version"] == "4"):
            self._maskStep += 1

        self["instance"].seek(0)

    def read_step(self, step):
        self["instance"].seek(self._headerSize + step * self._frameSize)

        data = self["instance"].read(self._configHeaderSize).splitlines()

        line = data[0].split()
        currentStep = int(line[1])

        timeStep = (currentStep - self._firstStep) * self._timeStep
        if self["imcon"] > 0:
            cell = " ".join(data[1:]).split()
            cell = np.array(cell, dtype=np.float64)
            cell = np.reshape(cell, (3, 3)).T
            cell *= measure(1.0, "ang").toval("nm")
        else:
            cell = None

        data = np.array(self["instance"].read(self._configSize).split())

        mask = np.ones((len(data),), dtype=np.bool)
        mask[0 :: self._maskStep] = False
        mask[1 :: self._maskStep] = False
        mask[2 :: self._maskStep] = False
        mask[3 :: self._maskStep] = False
        if (self["version"] == "3") or (self["version"] == "4"):
            mask[4 :: self._maskStep] = False

        config = np.array(np.compress(mask, data), dtype=np.float64)

        config = np.reshape(config, (self["natms"], 3 * (self["keytrj"] + 1)))

        config[:, 0:3] *= measure(1.0, "ang").toval("nm")

        # Case of the velocities
        if self["keytrj"] == 1:
            config[:, 3:6] *= measure(1.0, "ang/ps").toval("nm/ps")

        # Case of the velocities + gradients
        elif self["keytrj"] == 2:
            config[:, 3:6] *= measure(1.0, "ang/ps").toval("nm/ps")
            config[:, 6:9] *= measure(1.0, "uma ang / ps2").toval("uma nm / ps2")

        return timeStep, cell, config

    def close(self):
        self["instance"].close()


class DL_POLY(Converter):
    """
    Converts a DL_POLY trajectory to a HDF trajectory.
    """

    label = "DL-POLY"

    settings = collections.OrderedDict()
    settings["field_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "FIELD files|FIELD*|All files|*",
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "DL_Poly", "FIELD_cumen"
            ),
            "label": "Input FIELD file",
        },
    )
    settings["history_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "HISTORY files|HISTORY*|All files|*",
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "DL_Poly", "HISTORY_cumen"
            ),
            "label": "Input HISTORY file",
        },
    )
    settings["atom_aliases"] = (
        "PythonObjectConfigurator",
        {"default": {}, "label": "Atom aliases (Python dictionary)"},
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["version"] = (
        "SingleChoiceConfigurator",
        {"choices": list(_HISTORY_FORMAT.keys()), "default": "2", "label": "Version"},
    )
    # settings['output_files'] = ('output_files', {'formats':["HDFFormat"]})
    settings["output_file"] = (
        "OutputFilesConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "history_file",
            "label": "Output trajectory file name",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        self._fieldFile = FieldFile(
            self.configuration["field_file"]["filename"], aliases=self._atomicAliases
        )

        self._historyFile = HistoryFile(
            self.configuration["history_file"]["filename"],
            self.configuration["version"]["value"],
        )

        # The number of steps of the analysis.
        self.numberOfSteps = self._historyFile["n_frames"]

        self._chemicalSystem = ChemicalSystem()

        self._fieldFile.build_chemical_system(self._chemicalSystem)

        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["files"][0],
            self._chemicalSystem,
            self.numberOfSteps,
        )

        self._velocities = None

        self._gradients = None

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        # The x, y and z values of the current frame.
        time, unitCell, config = self._historyFile.read_step(index)

        unitCell = UnitCell(unitCell)

        if self._historyFile["imcon"] > 0:
            conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, config[:, 0:3], unitCell
            )
        else:
            conf = RealConfiguration(self._trajectory.chemical_system, config[:, 0:3])

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        if self._velocities is not None:
            conf["velocities"] = config[:, 3:6]

        if self._gradients is not None:
            conf["gradients"] = config[:, 6:9]

        self._trajectory.chemical_system.configuration = conf

        self._trajectory.dump_configuration(
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
                "gradients": "uma nm/ps2",
            },
        )

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

        self._historyFile.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(DL_POLY, self).finalize()
