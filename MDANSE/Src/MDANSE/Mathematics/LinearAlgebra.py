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
        elif is_tensor(other):
            product = Tensor(self.array).dot(other)
            if product.rank == 1:
                return Vector(product.array)
            else:
                return product
        elif hasattr(other, "_product_with_vector"):
            return other._product_with_vector(self)
        else:
            return Vector(np.multiply(self.array, other))

    def __rmul__(self, other):
        if is_tensor(other):
            product = other.dot(Tensor(self.array))
            if product.rank == 1:
                return Vector(product.array)
            else:
                return product
        else:
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

    def asTensor(self):
        """
        @returns: an equivalent rank-1 tensor object
        @rtype: L{Scientific.Geometry.Tensor}
        """
        return Tensor(self.array, 1)

    def dyadic_product(self, other):
        """
        @param other: a vector or a tensor
        @type other: L{Vector} or L{Scientific.Geometry.Tensor}
        @returns: the dyadic product with other
        @rtype: L{Scientific.Geometry.Tensor}
        @raises TypeError: if other is not a vector or a tensor
        """

        if is_vector(other):
            return Tensor(self.array[:, np.newaxis] * other.array[np.newaxis, :], 1)
        elif is_tensor(other):
            return Tensor(self.array, 1) * other
        else:
            raise TypeError("Dyadic product with non-vector")

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


class Quaternion:
    """
    Quaternion (hypercomplex number)

    This implementation of quaternions is not complete; only the features
    needed for representing rotation matrices by quaternions are
    implemented.

    Quaternions support addition, subtraction, and multiplication,
    as well as multiplication and division by scalars. Division
    by quaternions is not provided, because quaternion multiplication
    is not associative. Use multiplication by the inverse instead.

    The four components can be extracted by indexing.
    """

    def __init__(self, *data):
        """
        There are two calling patterns:

         - Quaternion(q0, q1, q2, q3)  (from four real components)

         - Quaternion(q)  (from a sequence containing the four components)
        """
        if len(data) == 1:
            self.array = np.array(data[0])
        elif len(data) == 4:
            self.array = np.array(data)

    def __getitem__(self, item):
        return self.array[item]

    def __add__(self, other):
        return Quaternion(self.array + other.array)

    def __sub__(self, other):
        return Quaternion(self.array - other.array)

    def __mul__(self, other):
        if is_quaternion(other):
            return Quaternion(np.dot(self.asMatrix(), other.asMatrix())[:, 0])
        else:
            return Quaternion(self.array * other)

    def __rmul__(self, other):
        if is_quaternion(other):
            raise ValueError("Not yet implemented")
        return Quaternion(self.array * other)

    def __div__(self, other):
        if is_quaternion(other):
            raise ValueError("Division by quaternions is not allowed.")
        return Quaternion(self.array / other)

    __truediv__ = __div__

    def __rdiv__(self, other):
        raise ValueError("Division by quaternions is not allowed.")

    def __repr__(self):
        return "Quaternion(" + str(list(self.array)) + ")"

    def __eq__(self, other):
        if isinstance(other, Quaternion):
            return np.all(self.array == other.array)
        else:
            return False

    def __hash__(self) -> int:
        return hash(tuple(self.array))

    def dot(self, other):
        return np.add.reduce(self.array * other.array)

    def norm(self):
        """
        @returns: the norm
        @rtype: C{float}
        """
        return np.sqrt(self.dot(self))

    def normalized(self):
        """
        @returns: the quaternion scaled such that its norm is 1
        @rtype: L{Quaternion}
        """
        return self / self.norm()

    def inverse(self):
        """
        @returns: the inverse
        @rtype: L{Quaternion}
        """
        inverse = np.linalg.inv(self.asMatrix())
        return Quaternion(inverse[:, 0])

    def asMatrix(self):
        """
        @returns: a 4x4 matrix representation
        @rtype: C{Numeric.array}
        """
        return np.dot(self._matrix, self.array)

    _matrix = np.zeros((4, 4, 4))
    _matrix[0, 0, 0] = 1
    _matrix[0, 1, 1] = -1
    _matrix[0, 2, 2] = -1
    _matrix[0, 3, 3] = -1
    _matrix[1, 0, 1] = 1
    _matrix[1, 1, 0] = 1
    _matrix[1, 2, 3] = -1
    _matrix[1, 3, 2] = 1
    _matrix[2, 0, 2] = 1
    _matrix[2, 1, 3] = 1
    _matrix[2, 2, 0] = 1
    _matrix[2, 3, 1] = -1
    _matrix[3, 0, 3] = 1
    _matrix[3, 1, 2] = -1
    _matrix[3, 2, 1] = 1
    _matrix[3, 3, 0] = 1

    def asRotation(self):
        """
        @returns: the corresponding rotation matrix
        @rtype: L{Scientific.Geometry.Transformation.Rotation}
        @raises ValueError: if the quaternion is not normalized
        """
        from MDANSE.Mathematics.Transformation import Rotation

        if np.fabs(self.norm() - 1.0) > 1.0e-5:
            raise ValueError("Quaternion not normalized")
        d = np.dot(np.dot(self._rot, self.array), self.array)
        return Rotation(d)

    _rot = np.zeros((3, 3, 4, 4))
    _rot[0, 0, 0, 0] = 1
    _rot[0, 0, 1, 1] = 1
    _rot[0, 0, 2, 2] = -1
    _rot[0, 0, 3, 3] = -1
    _rot[1, 1, 0, 0] = 1
    _rot[1, 1, 1, 1] = -1
    _rot[1, 1, 2, 2] = 1
    _rot[1, 1, 3, 3] = -1
    _rot[2, 2, 0, 0] = 1
    _rot[2, 2, 1, 1] = -1
    _rot[2, 2, 2, 2] = -1
    _rot[2, 2, 3, 3] = 1
    _rot[0, 1, 1, 2] = 2
    _rot[0, 1, 0, 3] = -2
    _rot[0, 2, 0, 2] = 2
    _rot[0, 2, 1, 3] = 2
    _rot[1, 0, 0, 3] = 2
    _rot[1, 0, 1, 2] = 2
    _rot[1, 2, 0, 1] = -2
    _rot[1, 2, 2, 3] = 2
    _rot[2, 0, 0, 2] = -2
    _rot[2, 0, 1, 3] = 2
    _rot[2, 1, 0, 1] = 2
    _rot[2, 1, 2, 3] = 2


class Tensor:
    """Tensor in 3D space

    Tensors support the usual arithmetic operations
    ('t1', 't2': tensors, 'v': vector, 's': scalar):

     -  't1+t2'        (addition)
     -  't1-t2'        (subtraction)
     -  't1*t2'        (tensorial (outer) product)
     -  't1*v'         (contraction with a vector, same as t1.dot(v.asTensor()))
     -  's*t1', 't1*s' (multiplication with a scalar)
     -  't1/s'         (division by a scalar)

    The coordinates can be extracted by indexing; a tensor of rank N
    can be indexed like an array of dimension N.

    Tensors are I{immutable}, i.e. their elements cannot be changed.

    Tensor elements can be any objects on which the standard
    arithmetic operations are defined. However, eigenvalue calculation
    is supported only for float elements.
    """

    def __init__(self, elements, nocheck=None):
        """
        @param elements: 2D array or nested list specifying the nine
                         tensor components
                         [[xx, xy, xz], [yx, yy, yz], [zx, zy, zz]]
        @type elements: C{Numeric.array} or C{list}
        """
        self.array = np.array(elements)
        if nocheck is None:
            if not np.logical_and.reduce(np.equal(np.array(self.array.shape), 3)):
                raise ValueError("Tensor must have length 3 along any axis")
        self.rank = len(self.array.shape)

    def __repr__(self):
        return "Tensor(" + str(self) + ")"

    def __str__(self):
        return str(self.array)

    def __add__(self, other):
        return Tensor(self.array + other.array, 1)

    __radd__ = __add__

    def __neg__(self):
        return Tensor(-self.array, 1)

    def __sub__(self, other):
        return Tensor(self.array - other.array, 1)

    def __rsub__(self, other):
        return Tensor(other.array - self.array, 1)

    def __mul__(self, other):
        if is_tensor(other):
            a = self.array[self.rank * (slice(None),) + (np.newaxis,)]
            b = other.array[other.rank * (slice(None),) + (np.newaxis,)]
            return Tensor(np.inner(a, b), 1)
        elif is_vector(other):
            return other.__rmul__(self)
        else:
            return Tensor(self.array * other, 1)

    def __rmul__(self, other):
        return Tensor(self.array * other, 1)

    def __div__(self, other):
        if is_tensor(other):
            raise TypeError("Can't divide by a tensor")
        else:
            return Tensor(self.array / (1.0 * other), 1)

    __truediv__ = __div__

    def __rdiv__(self, other):
        raise TypeError("Can't divide by a tensor")

    def __cmp__(self, other):
        if not is_tensor(other):
            return NotImplemented
        if self.rank != other.rank:
            return 1
        else:
            return not np.logical_and.reduce(np.equal(self.array, other.array).flat)

    def __len__(self):
        return 3

    def __getitem__(self, index):
        elements = self.array[index]
        if type(elements) is type(self.array):
            return Tensor(elements)
        else:
            return elements

    def __eq__(self, other):
        if isinstance(other, Tensor):
            return np.all(self.array == other.array)
        else:
            return False

    def __hash__(self) -> int:
        return hash(tuple(tuple(row) for row in self.array))

    def asVector(self):
        """
        @returns: an equivalent vector object
        @rtype: L{Scientific.Geometry.Vector}
        @raises ValueError: if rank > 1
        """
        if self.rank == 1:
            return Vector(self.array)
        else:
            raise ValueError("rank > 1")

    def dot(self, other):
        """
        @returns: the contraction with other
        @rtype: L{Tensor}
        """
        if is_tensor(other):
            a = self.array
            b = np.transpose(other.array, list(range(1, other.rank)) + [0])
            return Tensor(np.inner(a, b), 1)
        else:
            return Tensor(self.array * other, 1)

    def diagonal(self, axis1=0, axis2=1):
        if self.rank == 2:
            return Tensor([self.array[0, 0], self.array[1, 1], self.array[2, 2]])
        else:
            if axis2 < axis1:
                axis1, axis2 = axis2, axis1
            raise ValueError("Not yet implemented")

    def trace(self, axis1=0, axis2=1):
        """
        @returns: the trace of the tensor
        @rtype: type of tensor elements
        @raises ValueError: if rank !=2
        """
        if self.rank == 2:
            return float(self.array[0, 0] + self.array[1, 1] + self.array[2, 2])
        else:
            raise ValueError("Not yet implemented")

    def transpose(self):
        """
        @returns: the transposed (index reversed) tensor
        @rtype: L{Tensor}
        """
        return Tensor(np.transpose(self.array))

    def symmetricalPart(self):
        """
        @returns: the symmetrical part of the tensor
        @rtype: L{Tensor}
        @raises ValueError: if rank !=2
        """
        if self.rank == 2:
            return Tensor(
                0.5 * (self.array + np.transpose(self.array, np.array([1, 0]))), 1
            )
        else:
            raise ValueError("Not yet implemented")

    def asymmetricalPart(self):
        """
        @returns: the asymmetrical part of the tensor
        @rtype: L{Tensor}
        @raises ValueError: if rank !=2
        """
        if self.rank == 2:
            return Tensor(
                0.5 * (self.array - np.transpose(self.array, np.array([1, 0]))), 1
            )
        else:
            raise ValueError("Not yet implemented")

    def eigenvalues(self):
        """
        @returns: the eigenvalues of the tensor
        @rtype: C{Numeric.array}
        @raises ValueError: if rank !=2
        """
        if self.rank == 2:
            return np.linalg.eigvals(self.array)
        else:
            raise ValueError("Undefined operation")

    def diagonalization(self):
        """
        @returns: the eigenvalues of the tensor and a tensor
                  representing the rotation matrix to the diagonal form
        @rtype: (C{Numeric.array}, L{Tensor})
        @raises ValueError: if rank !=2
        """
        if self.rank == 2:
            ev, vectors = np.linalg.eig(self.array)
            vectors = np.transpose(vectors)
            return ev, Tensor(vectors)
        else:
            raise ValueError("Undefined operation")

    def inverse(self):
        """
        @returns: the inverse of the tensor
        @rtype: L{Tensor}
        @raises ValueError: if rank !=2
        """
        if self.rank == 2:
            return Tensor(np.linalg.inv(self.array))
        else:
            raise ValueError("Undefined operation")


def is_tensor(x):
    """
    @returns: C{True} if x is a L{Tensor}
    """
    return isinstance(x, Tensor)


# Type check
def is_quaternion(x):
    """
    @param x: any object
    @type x: any
    @returns: C{True} if x is a quaternion
    """
    return isinstance(x, Quaternion)


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

delta = Tensor([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

epsilon = Tensor(
    [
        [[0, 0, 0], [0, 0, 1], [0, -1, 0]],
        [[0, 0, -1], [0, 0, 0], [1, 0, 0]],
        [[0, 1, 0], [-1, 0, 0], [0, 0, 0]],
    ]
)
