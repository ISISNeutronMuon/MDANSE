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
from typing import TYPE_CHECKING, TypedDict

import numpy as np
import numpy.typing as npt
from scipy.stats import truncnorm

from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    Configurable,
    ConfigureDescriptor,
)
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
    from MDANSE.Framework.Status import Status
    from MDANSE.MolecularDynamics.Trajectory import Trajectory
    from MDANSE.MolecularDynamics.UnitCell import UnitCell


class VectorDict(TypedDict):
    """Dictionary produced by vector generators."""

    q_vectors: npt.NDArray[np.floating]
    weights: npt.NDArray[np.floating]
    q: npt.NDArray[np.floating]
    hkls: npt.NDArray[np.floating] | None
    n_q_vectors: int
    n_q_found: int


GAUSS_WIDTH_FACTOR = 4.70964  # 2*sqrt(2*ln(2))
WIDTH_NONZERO_LIMIT = 1e-15  # width below this limit is assumed to be 0


def truncated_normal_distribution(
    n_elements: int,
    left_limit: float,
    right_limit: float,
    width: float,
    centre: float,
    rng: np.random.Generator,
    zero_width_limit: float = 0.1,
) -> npt.NDArray[float]:
    """Generate a normal distribution of values within the specified limits.

    Parameters
    ----------
    n_elements : int
        Number of values to be generated.
    left_limit : float
        Lower limit of the generated values.
    right_limit : float
        Upper limit of the generated values.
    width : float
        FWHM of the value distribution.
    centre : float
        Position of the maximum of the distribution.
    zero_width_limit : float, optional
        Limits used when width is 0 to guarantee non-zero domain width, by default 0.1.
    rng : np.random.Generator
        A numpy random number generator object.

    Returns
    -------
    npt.NDArray[float]
        A truncated normal distribution of points within the specified limits.
    """
    if np.isclose(width, 0, atol=WIDTH_NONZERO_LIMIT):
        return truncnorm.rvs(
            -zero_width_limit,
            zero_width_limit,
            loc=centre,
            scale=0,
            size=n_elements,
            random_state=rng,
        )
    return truncnorm.rvs(
        GAUSS_WIDTH_FACTOR * (left_limit - centre) / width,
        GAUSS_WIDTH_FACTOR * (right_limit - centre) / width,
        loc=centre,
        scale=width / GAUSS_WIDTH_FACTOR,
        size=n_elements,
        random_state=rng,
    )


def calculate_average_q_per_shell(vector_config: IQVectors) -> npt.NDArray[float]:
    r"""Calculates the average :math:`\mathbf{q}` per shell.

    The averaging uses the weights determined by sampling the reciprocal space.

    Parameters
    ----------
    vector_config : IQVectors
        An instance of a q-vector generator. A subclass of IQVectors.

    Returns
    -------
    npt.NDArray[float]
        Array of average q per shell.
    """
    results = np.empty(len(vector_config.q_vectors))
    for shell_index, shell_dict in enumerate(vector_config.q_vectors.values()):
        if shell_dict is None or len(shell_dict["q_vectors"]) == 0:
            results[shell_index] = np.nan
            continue
        results[shell_index] = np.average(
            np.linalg.norm(shell_dict["q_vectors"], axis=0),
            weights=shell_dict["weights"],
        )
    return results


class IQVectors(Configurable, metaclass=SubclassFactory):
    """Parent class of all Q vector generators."""

    q_vectors: dict[float, VectorDict | None]

    is_lattice = False
    depends = {}

    def __init__(
        self,
        *,
        trajectory: Trajectory | None = None,
        unit_cell: UnitCell | None = None,
        status: Status | None = None,
    ):
        super().__init__()

        if unit_cell and trajectory:
            raise ValueError("Both cell and trajectory provided")

        if trajectory:
            unit_cell = trajectory.unit_cell(0)

        self._unit_cell = unit_cell

        self._status = status
        self.q_vectors = {}

    @property
    def n_shells(self) -> int:
        return len(self.shells)

    @abc.abstractmethod
    def _generate(self):
        raise NotImplementedError("Q vector generator has no _generate method")

    def generate(self) -> bool:
        """Generate vectors by calling the internal method _generate."""
        self._generate()

        if self._status is not None:
            self._status.finish()
            return True
        LOG.error(
            "Cannot generate vectors: q vector generator is not configured correctly.",
        )
        return False

    def validate(self, conf: ConfigureDescriptor, value: Configurable):
        try:
            # Force the setting (if we've reached this far)
            setattr(self, conf.private_name, value)
            self.generate()
        except Exception as err:
            import traceback

            traceback.print_exception(err)
            raise ConfigError("Invalid or incomplete QVector configuration.") from err
        return value

    @classmethod
    def qvectors_to_hkl(
        cls,
        vector_array: npt.NDArray[np.floating],
        unit_cell: UnitCell,
    ) -> npt.NDArray[np.floating]:
        """Recalculate Q vectors to HKL Miller indices.

        Using a unit cell definition, recalculates an array
        of q vectors to an equivalent array of HKL Miller indices.

        Parameters
        ----------
        vector_array : npt.NDArray[np.floating]
            a (3,N) array of scattering vectors
        unit_cell : UnitCell
            an instance of UnitCell class describing the simulation box

        Returns
        -------
        npt.NDArray[np.floating]
            A (3,N) array of HKL values (Miller indices)

        """
        return np.dot(unit_cell.direct, vector_array) / (2 * np.pi)

    @classmethod
    def hkl_to_qvectors(
        cls, hkls: npt.NDArray[np.floating], unit_cell: UnitCell
    ) -> npt.NDArray[np.floating]:
        """Convert an array of HKL values to scattering vectors.

        Uses a unit cell object to get the lattice vectors for conversion.

        Parameters
        ----------
        hkls : npt.NDArray[np.floating]
            A (3,N) array of HKL values (Miller indices)
        unit_cell : UnitCell
            An instance of UnitCell class describing the simulation box shape

        Returns
        -------
        npt.NDArray[np.floating]
            a (3, N) array of Q vectors (scattering vectors)

        """
        return 2 * np.pi * np.dot(unit_cell.inverse, hkls)

    @classmethod
    def lattice_vectors_with_weights(
        cls,
        start_shape: npt.NDArray[np.floating],
        unit_cell: UnitCell,
    ) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]:
        """Return HKL vectors from the input q-vector array.

        An arbitrary shape will be scaled by values between qmin and qmax
        to populate all the integer-index HKL values in the shell.

        Parameters
        ----------
        start_shape : npt.NDArray[np.floating]
            Q-vector array representing a specific geometric shape.
        unit_cell : UnitCell
            The unit cell of the system, for conversion to HKL values.

        Returns
        -------
        tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]
            Unique Q-vectors as HKL values, number of times each vector appeared.
        """
        hkl_fractional = cls.qvectors_to_hkl(start_shape, unit_cell)
        return np.unique(np.round(hkl_fractional), return_counts=True, axis=1)

    @classmethod
    def vectors_within_limits(
        cls,
        q_vectors: npt.NDArray[np.floating],
        *,
        q_min: float,
        q_max: float,
    ) -> npt.NDArray[bool]:
        """Check which vectors in the input array have the length within the limits.

        Parameters
        ----------
        q_vectors : npt.NDArray[np.floating]
            Array containing vectors to be checked.
        q_min : float
            Lower limit of |q|
        q_max : float
            Upper limit of |q|

        Returns
        -------
        npt.NDArray[bool]
            Boolean mask array, True for vectors within limits.
        """
        lengths = np.linalg.norm(q_vectors, axis=0)
        return (lengths >= q_min) & (lengths <= q_max)

    def write_vectors_to_file(self, output_data: OutputData):
        """Write the vectors to output file as an array.

        Writes a summary of the generated vectors to the output
        file using an OutputData class instance.

        Parameters
        ----------
        output_data : OutputData
            An object managing the writeout to one or many output files

        """
        qvector_info = self.q_vectors

        q_values = [float(x) for x in qvector_info]
        output_data.add(
            "vector_generator/q",
            "LineOutputVariable",
            q_values,
            units="1/nm",
        )
        output_data.add(
            "vector_generator/average_q",
            "LineOutputVariable",
            calculate_average_q_per_shell(self),
            units="1/nm",
        )
        output_data.add(
            "vector_generator/coordinates",
            "LineOutputVariable",
            [0, 1, 2],
            units="au",
        )

        output_data.add(
            "vector_generator/n_q_vectors",
            "LineOutputVariable",
            [
                qvector_info[q]["n_q_vectors"] if qvector_info[q] is not None else 0
                for q in q_values
            ],
            units="au",
        )
        output_data.add(
            "vector_generator/n_q_found",
            "LineOutputVariable",
            [
                qvector_info[q]["n_q_found"] if qvector_info[q] is not None else 0
                for q in q_values
            ],
            units="au",
        )

        for nq, q in enumerate(q_values):
            current = f"vector_generator/shell_{nq}/qvector_array"
            output_data.add(
                current,
                "SurfaceOutputVariable",
                qvector_info[q]["q_vectors"] if qvector_info[q] is not None else [[]],
                units="1/nm",
                axis="vector_generator/coordinates|index",
            )

        for nq, q in enumerate(q_values):
            current = f"vector_generator/shell_{nq}/weights"
            output_data.add(
                current,
                "LineOutputVariable",
                qvector_info[q]["weights"] if qvector_info[q] is not None else [],
                units="au",
                axis="index",
            )

        for nq, q in enumerate(q_values):
            if (
                qvector_info[q] is not None
                and (data := qvector_info[q].get("hkls")) is not None
            ):
                current = f"vector_generator/shell_{nq}/hkl_array"
                output_data.add(
                    current,
                    "SurfaceOutputVariable",
                    data,
                    units="au",
                    axis="vector_generator/coordinates|index",
                )
