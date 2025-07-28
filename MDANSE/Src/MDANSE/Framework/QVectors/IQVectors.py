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

import abc
from typing import TYPE_CHECKING

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Configurable import Configurable
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
    from MDANSE.MolecularDynamics.UnitCell import UnitCell


class IQVectors(Configurable, metaclass=SubclassFactory):
    """Parent class of all Q vector generators."""

    is_lattice = False

    def __init__(self, atom_configuration, status=None):
        Configurable.__init__(self)

        self._atom_configuration = atom_configuration

        self._status = status

    @abc.abstractmethod
    def _generate(self):
        pass

    def generate(self) -> bool:
        """Generate vectors by calling the internal method _generate."""
        if self._configured:
            self._generate()

            if self._status is not None:
                self._status.finish()
            return True
        LOG.error(
            "Cannot generate vectors: q vector generator is not configured correctly.",
        )
        return False

    @classmethod
    def qvectors_to_hkl(
        self,
        vector_array: np.array,
        unit_cell: UnitCell,
    ) -> np.ndarray:
        """Recalculate Q vectors to HKL Miller indices.

        Using a unit cell definition, recalculates an array
        of q vectors to an equivalent array of HKL Miller indices.

        Parameters
        ----------
        vector_array : np.array
            a (3,N) array of scattering vectors
        unit_cell : UnitCell
            an instance of UnitCell class describing the simulation box

        Returns
        -------
        np.ndarray
            A (3,N) array of HKL values (Miller indices)

        """
        return np.dot(unit_cell.direct, vector_array) / (2 * np.pi)

    @classmethod
    def hkl_to_qvectors(self, hkls: np.array, unit_cell: UnitCell) -> np.ndarray:
        """Convert an array of HKL values to scattering vectors.

        Uses a unit cell object to get the lattice vectors for conversion.

        Parameters
        ----------
        hkls : np.array
            A (3,N) array of HKL values (Miller indices)
        unit_cell : UnitCell
            An instance of UnitCell class describing the simulation box shape

        Returns
        -------
        np.ndarray
            a (3, N) array of Q vectors (scattering vectors)

        """
        return 2 * np.pi * np.dot(unit_cell.inverse, hkls)

    def write_vectors_to_file(self, output_data: OutputData):
        """Write the vectors to output file as an array.

        Writes a summary of the generated vectors to the output
        file using an OutputData class instance.

        Parameters
        ----------
        output_data : OutputData
            An object managing the writeout to one or many output files

        """
        qvector_info = self._configuration["q_vectors"]
        q_values = [float(x) for x in qvector_info]
        output_data.add(
            "vector_generator/q",
            "LineOutputVariable",
            q_values,
            units="1/nm",
        )
        output_data.add(
            "vector_generator/coordinates",
            "LineOutputVariable",
            [0, 1, 2],
            units="au",
        )

        for nq, q in enumerate(q_values):
            current = f"vector_generator/shell_{nq}/qvector_array"
            output_data.add(
                current,
                "SurfaceOutputVariable",
                qvector_info[q]["q_vectors"],
                units="1/nm",
                axis="vector_generator/coordinates|index",
            )

        for nq, q in enumerate(q_values):
            if (data := qvector_info[q].get("hkls")) is not None:
                current = f"vector_generator/shell_{nq}/hkl_array"
                output_data.add(
                    current,
                    "SurfaceOutputVariable",
                    data,
                    units="au",
                    axis="vector_generator/coordinates|index",
                )
