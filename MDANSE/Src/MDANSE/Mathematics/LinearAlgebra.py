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


def cmp(a, b):
    return (a > b) - (a < b)


class Vector:
    """Vector in 3D space

    Constructor:


    Vectors support the usual arithmetic operations
    ('v1', 'v2': vectors, 's': scalar):

     -  'v1+v2'           (addition)
     -  'v1-v2'           (subtraction)
     -  'v1*v2'           (scalar product)
     -  's*v1', 'v1*s'    (multiplication with a scalar)
     -  'v1/s'            (division by a scalar)

    The three coordinates can be extracted by indexing.

    Vectors are B{immutable}, i.e. their elements cannot be changed.

    Vector elements can be any objects on which the standard
    arithmetic operations plus the functions sqrt and arccos are defined.
    """

    def __init__(self, x=None, y=None, z=None):
        """
        There are two supported calling patterns:
         1. C{Vector(x, y, z)}
            (from three coordinates)
         2. C{Vector(coordinates)}
            (from any sequence containing three coordinates)
        """
        if x is None:
            self.array = [0.0, 0.0, 0.0]
        elif y is None and z is None:
            self.array = x
        else:
            self.array = [x, y, z]
        self.array = np.array(self.array)

    def __getstate__(self):
        return list(self.array)

    def __setstate__(self, state):
        self.array = np.array(state)

    def __copy__(self, memo=None):
        return self

    __deepcopy__ = __copy__

    def __repr__(self):
        return f"Vector({','.join(map(repr, self.array))})"

    def __str__(self):
        return repr(list(self.array))

    def __add__(self, other):
        return Vector(self.array + other.array)

    __radd__ = __add__

    def __neg__(self):
        return Vector(-self.array)

    def __sub__(self, other):
        return Vector(self.array - other.array)

    def __rsub__(self, other):
        return Vector(other.array - self.array)

    def __mul__(self, other):
        if is_vector(other):
            return float(np.add.reduce(self.array * other.array))
        elif hasattr(other, "_product_with_vector"):
            return other._product_with_vector(self)
        else:
            return Vector(np.multiply(self.array, other))

    def __rmul__(self, other):
        return Vector(np.multiply(self.array, other))

    def __div__(self, other):
        if is_vector(other):
            raise TypeError("Can't divide by a vector")
        else:
            return Vector(np.divide(self.array, 1.0 * other))

    __truediv__ = __div__

    def __rdiv__(self, other):
        raise TypeError("Can't divide by a vector")

    def __cmp__(self, other):
        if is_vector(other):
            return cmp(np.add.reduce(abs(self.array - other.array)), 0)
        return NotImplemented

    def __len__(self):
        return 3

    def __getitem__(self, index):
        return self.array[index]

    def __eq__(self, other):
        if isinstance(other, Vector):
            return np.all(self.array == other.array)
        else:
            return False

    def __hash__(self) -> int:
        return hash(tuple(self.array))

    def x(self):
        """
        @returns: the x coordinate
        @rtype: type of vector elements
        """
        return self.array[0]

    def y(self):
        """
        @returns: the y coordinate
        @rtype: type of vector elements
        """
        return self.array[1]

    def z(self):
        """
        @returns: the z coordinate
        @rtype: type of vector elements
        """
        return self.array[2]

    def length(self):
        """
        @returns: the length (norm) of the vector
        @rtype: type of vector elements
        """
        return np.sqrt(np.add.reduce(self.array * self.array))

    def normal(self):
        """
        @returns: a normalized (length 1) copy of the vector
        @rtype: L{Vector}
        @raises ZeroDivisionError: if vector length is zero
        """
        len = np.sqrt(np.add.reduce(self.array * self.array))
        if len == 0:
            raise ZeroDivisionError("Can't normalize a zero-length vector")
        return Vector(np.divide(self.array, len))

    def cross(self, other):
        """
        @param other: a vector
        @type other: L{Vector}
        @returns: cross product with other
        @rtype: L{Vector}
        """
        if not is_vector(other):
            raise TypeError("Cross product with non-vector")
        return Vector(
            self.array[1] * other.array[2] - self.array[2] * other.array[1],
            self.array[2] * other.array[0] - self.array[0] * other.array[2],
            self.array[0] * other.array[1] - self.array[1] * other.array[0],
        )

    def angle(self, other):
        """
        @param other: a vector
        @type other: L{Vector}
        @returns: the angle to other
        @rtype: C{float}
        @raises TypeError: if other is not a vector
        """
        if not is_vector(other):
            raise TypeError("Angle between vector and non-vector")
        cosa = np.add.reduce(self.array * other.array) / np.sqrt(
            np.add.reduce(self.array * self.array)
            * np.add.reduce(other.array * other.array)
        )
        cosa = max(-1.0, min(1.0, cosa))
        return np.arccos(cosa)


# Type check


def is_vector(x):
    """
    @returns: C{True} if x is a L{Vector}
    """

    return isinstance(x, Vector)


ex = Vector(1.0, 0.0, 0.0)

ey = Vector(0.0, 1.0, 0.0)

ez = Vector(0.0, 0.0, 1.0)

nullVector = Vector(0.0, 0.0, 0.0)
