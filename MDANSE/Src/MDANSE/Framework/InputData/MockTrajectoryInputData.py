# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InputData/HDFTrajectoryInputData.py
# @brief     Implements module/class/test HDFTrajectoryInputData
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData
from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory


class MockTrajectoryInputData(InputFileData):
    extension = "json"

    def load(self):
        try:
            traj = MockTrajectory.from_json(self._name)
        except IOError as e:
            raise InputDataError(str(e))
        except ValueError as e:
            raise InputDataError(str(e))

        self._data = traj

    def close(self):
        self._data.close()

    def info(self):
        val = []

        val.append("Path:")
        val.append("%s\n" % self._name)
        val.append("Number of steps:")
        val.append("%s\n" % len(self._data))
        val.append("Configuration:")
        val.append(
            "\tIs periodic: {}\n".format(
                "unit_cell" in self._data.file["/configuration"]
            )
        )
        val.append("Variables:")
        for k, v in self._data.file["/configuration"].items():
            val.append("\t- {}: {}".format(k, v.shape))

        mol_types = {}
        val.append("\nMolecular types found:")
        for ce in self._data.chemical_system.chemical_entities:
            if ce.__class__.__name__ in mol_types:
                mol_types[ce.__class__.__name__] += 1
            else:
                mol_types[ce.__class__.__name__] = 1

        for k, v in mol_types.items():
            val.append("\t- {:d} {}".format(v, k))

        val = "\n".join(val)

        return val

    @property
    def trajectory(self):
        return self._data

    @property
    def chemical_system(self):
        return self._data.chemical_system

    @property
    def hdf(self):
        return self._data.file
