import itertools
from abc import abstractmethod
from collections.abc import Callable, Generator, Iterable, Iterator
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import NewType, Optional, Tuple

import numpy as np
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from numpy.typing import ArrayLike, NDArray

ThreeVector = NewType("ThreeVector", ArrayLike)


@dataclass
class QVectorData:
    """Data relating to a single Q-Vector

    Returned from a QVectorGenerator"""

    q: NDArray[float]
    mod_q: float
    hkl: Optional[NDArray[int]]
    hkl_exact: Optional[NDArray[float]]

    def __init__(self, q: ThreeVector, lattice: Optional[UnitCell] = None):
        self.q = np.array(q, dtype=float)
        self.mod_q = np.linalg.norm(q)

        if lattice is not None:
            self.hkl_exact = np.dot(lattice.direct, q)
            self.hkl = np.rint(self.hkl_exact)
        else:
            self.hkl_exact = None
            self.hkl = None

    def __eq__(self, other):
        return np.allclose(self.q, other.q)

    @classmethod
    def from_hkl(cls, hkl: ThreeVector, lattice: UnitCell):
        q = np.dot(lattice.inverse, hkl)
        return cls(q, lattice)

    @classmethod
    def from_q(cls, q: ThreeVector, lattice: Optional[UnitCell] = None):
        return cls(q, lattice)


QVecGen = Generator[QVectorData, int, None]
QVecGeneratorProtocol = Callable[[Optional[UnitCell]], QVecGen]


class QVectorGenerator(metaclass=SubclassFactory):
    """Abstract type for generation of Q-Vectors."""

    def __init__(
        self, *, hkl: bool = False, lattice: Optional[UnitCell] = None, **kwargs
    ):
        if hkl and lattice is None:
            raise ValueError("`hkl` requires defined `lattice`")

        self.lattice = lattice
        self.hkl = hkl
        self._ind = 0

    @property
    def qvec_gen(self):
        return QVectorData.from_hkl if self.hkl else QVectorData.from_q

    def __iter__(self):
        return self.generate()

    @singledispatchmethod
    def __getitem__(self, s):
        """Get a subset of the Qvectors

        Parameters
        ----------
        s : Union[slice, int]
            If :class:`slice`, get that subset.
            If :class:`int`, get the first N vectors.

        Examples
        --------
        >>> from MDANSE.Framework.NewQVectors.LinearQVectors import LinearQVectors
        >>> vec = LinearQVectors([1, 0, 0])
        >>> [qvec.mod_q for qvec in vec[3]]
        [1., 2., 3.]
        >>> [qvec.mod_q for qvec in vec[4:6]]
        [4., 5.]
        """
        raise NotImplementedError(f"Cannot slice by {type(s).__name__}")

    @__getitem__.register(slice)
    def _(self, s):
        return itertools.islice(self.generate(), s.start, s.stop, s.step)

    @__getitem__.register(int)
    def _(self, n):
        return self.generate_n(n)

    def generate_n(self, n: int) -> Iterator[QVectorData]:
        """Generate a set of N Q-Vectors with default arguments.

        Parameters
        ----------
        n : int
            Number of Q-Vectors to generate.
        """
        if n is None:
            raise ValueError("n cannot be None")
        return itertools.islice(self.generate(), n)

    def generate(
        self,
        *,
        radius: Optional[Tuple[float, float]] = None,
        lattice: Optional[UnitCell] = None,
    ) -> QVecGen:
        """Generate Q Vectors filtered to lie within shell.

        Parameters
        ----------
        radius : Optional[Tuple[float, float]]
            Min-max of radius to be included in output set.
        lattice : Optional[UnitCell]
            Lattice to generate data on.

        Yields
        ------
        QVectorData
            Q-Points in regime.

        Notes
        -----
        In case of specific optimisation for generating within a radius
        overload this function.
        """
        lattice = lattice if lattice is not None else self.lattice

        vectors = self._generate(lattice=lattice)
        if radius is not None:
            vectors = filter(lambda qvec: radius[0] < qvec.q < radius[1], vectors)

        yield from vectors

    @abstractmethod
    def shells(self, shells: Iterable[tuple[float, float]], n_per: int, lattice: Optional[UnitCell] = None) -> QVecGen:
        """Underlying specific Q-Vector generator.

        Parameters
        ----------
        lattice : Optional[UnitCell]
            Lattice to generate data in.

        Yields
        ------
        QVectorData
            Q-Points in regime.
        """
        for mini, maxi in shells:
            yield from itertools.islice(
                filter(
                    lambda x: mini < x.mod_q < maxi, self._generate(lattice=lattice)
                ),
                n_per,
            )

    @abstractmethod
    def _generate(self, lattice: Optional[UnitCell] = None) -> QVecGen:
        """Underlying specific Q-Vector generator.

        Parameters
        ----------
        lattice : Optional[UnitCell]
            Lattice to generate data in.

        Yields
        ------
        QVectorData
            Q-Points in regime.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self, value: int = 0):
        """Reset generator to a given state.

        Parameters
        ----------
        value : int
            State to initialise to.

        Notes
        -----
        Some generators may not support non-0 resets
        others may not support reset at all.
        """
        self._ind = value

    @property
    def index(self):
        return self._ind

    @index.setter
    def index(self, value):
        self.reset(value)
