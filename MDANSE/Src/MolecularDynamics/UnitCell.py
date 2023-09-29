import numpy as np
from numpy.typing import ArrayLike


class UnitCell:
    """
    This class stores a unit cell, which is stored row-wise i.e. the a, b and c vectors are
    respectively the first, second and third row of the unit cell matrix.
    """

    def __init__(self, unit_cell: ArrayLike) -> None:
        """
        The constructor.

        :param unit_cell: the unit cell matrix
        :type unit_cell: 3x3 numpy array
        """

        self._unit_cell = np.array(unit_cell).astype(np.float64)

        if self._unit_cell.shape != (3, 3):
            raise ValueError(
                f"the unit cell must have a shape of 3×3 but {self._unit_cell.shape} was provided."
            )

        self._inverse_unit_cell = np.linalg.pinv(self._unit_cell)

    def __eq__(self, other: "UnitCell") -> bool:
        if isinstance(other, UnitCell):
            return np.allclose(self._unit_cell, other._unit_cell)
        else:
            return False

    def __repr__(self) -> str:
        return f"MDANSE.MolecularDynamics.UnitCell.UnitCell({repr(self._unit_cell)})"

    @property
    def a_vector(self) -> np.ndarray:
        """
        Return the a vector.

        :return: the a vector
        :rtype: numpy.ndarray
        """
        return self._unit_cell[0, :]

    @property
    def b_vector(self) -> np.ndarray:
        """
        Return the b vector.

        :return: the b vector
        :rtype: numpy.ndarray
        """
        return self._unit_cell[1, :]

    @property
    def c_vector(self) -> np.ndarray:
        """Return the c vector.

        :return: the c vector
        :rtype: numpy.ndarray
        """
        return self._unit_cell[2, :]

    @property
    def direct(self) -> np.ndarray:
        """
        Return the unit cell matrix.

        :return: the unit cell matrix
        :rtype: numpy.ndarray
        """
        return self._unit_cell

    @property
    def inverse(self) -> np.ndarray:
        """
        Return the inverse of the unit cell matrix.

        :return: the inverse of the unit cell matrix
        :rtype: numpy.ndarray
        """
        return self._inverse_unit_cell

    @property
    def transposed_direct(self) -> np.ndarray:
        """
        Return the transposed of the unit cell matrix.

        :return: the transposed of the unit cell matrix
        :rtype: numpy.ndarray
        """
        return self._unit_cell.T

    @property
    def transposed_inverse(self) -> np.ndarray:
        """
        Return the transposed of the inverse of unit cell matrix.

        :return: the transposed of the inverse of the unit cell matrix
        :rtype: numpy.ndarray
        """

        return self._inverse_unit_cell.T

    @property
    def volume(self) -> float:
        """
        Return the volume unit cell matrix.

        :return: the volume of the unit cell
        :rtype: float
        """

        return np.abs(
            np.dot(
                np.cross(self._unit_cell[0, :], self._unit_cell[1, :]),
                self._unit_cell[2, :],
            )
        )
