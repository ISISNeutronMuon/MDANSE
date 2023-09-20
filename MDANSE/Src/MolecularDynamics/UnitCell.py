import numpy as np
from icecream import ic


class UnitCell:
    """This class stores a unit cell. is stored row-wise i.e. the a, b and c vectors are
    respectively the first, second and thrid row of the unit cell matrix.
    """

    def __init__(self, unit_cell):
        """The constructor.

        :param unit_cell: the unit cell matrix
        :type unit_cell: 3x3 numpy array
        """
        ic(f"UnitCell received {unit_cell}")
        self._unit_cell = np.array(unit_cell).astype(np.float64)
        ic(f"UnitCell saved self._unit_cell")
        self._inverse_unit_cell = np.linalg.pinv(self._unit_cell)
        ic(f"UnitCell saved self._inverse_unit_cell as {self._inverse_unit_cell}")

    @property
    def a_vector(self):
        """Return the a vector.

        :return: the a vector
        :rtype: numpy array
        """
        return self._unit_cell[0, :]

    @property
    def b_vector(self):
        """Return the b vector.

        :return: the b vector
        :rtype: numpy array
        """
        return self._unit_cell[1, :]

    @property
    def c_vector(self):
        """Return the c vector.

        :return: the c vector
        :rtype: numpy array
        """
        return self._unit_cell[2, :]

    @property
    def direct(self):
        """Return the unit cell matrix.

        :return: the unit cell matrix
        :rtype: numpy array
        """
        return self._unit_cell

    @property
    def inverse(self):
        """Return the inverse of the unit cell matrix.

        :return: the inverse of the unit cell matrix
        :rtype: numpy array
        """
        return self._inverse_unit_cell

    @property
    def transposed_direct(self):
        """Return the transposed of the unit cell matrix.

        :return: the transposed of the unit cell matrix
        :rtype: numpy array
        """
        return self._unit_cell.T

    @property
    def transposed_inverse(self):
        """Return the transposed of the inverse of unit cell matrix.

        :return: the transposed of the inverse of the unit cell matrix
        :rtype: numpy array
        """

        return self._inverse_unit_cell.T

    @property
    def volume(self):
        """Return the volume unit cell matrix.

        :return: the volume
        :rtype: float
        """

        return np.abs(
            np.dot(
                np.cross(self._unit_cell[0,:],self._unit_cell[1,:]),
                self._unit_cell[2,:])
            )

    @property
    def abc_and_angles(self):
        a,b,c = self.a_vector, self.b_vector, self.c_vector
        abc = [np.linalg.norm(vector) for vector in [a,b,c]]
        alpha = np.linalg.norm(np.cross(b,c))/(abc[1]*abc[2])
        beta = np.linalg.norm(np.cross(c,a))/(abc[2]*abc[0])
        gamma = np.linalg.norm(np.cross(a,b))/(abc[0]*abc[1])
        angles = np.degrees(np.arcsin([alpha, beta, gamma]))
        return *abc, *angles
