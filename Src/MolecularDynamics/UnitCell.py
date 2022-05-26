import numpy as np

class UnitCell:

    def __init__(self,unit_cell):

        self._unit_cell = unit_cell

        self._inverse_unit_cell = np.linalg.inv(self._unit_cell)

    @property
    def a_vector(self):
        return self._unit_cell[0,:]

    @property
    def b_vector(self):
        return self._unit_cell[1,:]

    @property
    def c_vector(self):
        return self._unit_cell[2,:]

    @property
    def direct(self):

        return self._unit_cell

    @property
    def inverse(self):

        return self._inverse_unit_cell

    @property
    def transposed_direct(self):

        return self._unit_cell.T

    @property
    def transposed_inverse(self):

        return self._inverse_unit_cell.T

    @property
    def volume(self):

        return np.abs(
            np.dot(
                np.cross(self._unit_cell[0,:],self._unit_cell[1,:]),
                self._unit_cell[2,:])
            )