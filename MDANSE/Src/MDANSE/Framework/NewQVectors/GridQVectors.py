from collections.abc import Generator, Sequence
from functools import partial
from itertools import product as cart_prod
from typing import Optional, Tuple, TypeVar, Union, NewType

import numpy as np
from MDANSE.Framework.NewQVectors.QVector import QVecGen, QVectorGenerator, ThreeVector
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from numpy.typing import ArrayLike, NDArray

T = TypeVar("T")
OneOrThree = Union[T, Tuple[T, T, T]]
Limits = Tuple[float, float]
GridSpec = NewType("GridSpec", OneOrThree[OneOrThree])


class GridQVectors(QVectorGenerator):
    """Generate a cuboidal grid of Q Vectors.

    Parameters
    ----------
    ranges : OneOrThree[OneOrThree]
        Start-stop-step data for grid.

        Can be specified as:

        - Scalar -- stop for xyz, ``start`` = ``0``, ``step`` = 1.
        - 2-tuple -- start-stop for xyz, ``step`` = 1.
        - 3-tuple -- start-stop-step for xyz.
        - 3x2-array -- start-stop for each dimension, ``step`` = 1.
        - 3x3-array -- start-stop-step for each dimension.

    origin : ThreeVector
        Origin of grid vectors.
    hkl : bool
        Whether grid is defined in reciprocal lattice units.
    lattice : Optional[UnitCell]
        Lattice to generate vectors for.

    Raises
    ------
    ValueError
        If ranges are the wrong shape.
        If hkl requested, but no lattice provided.

    Notes
    -----
    It should be noted that ``GridQVectors`` is subject to
    the precision of IEEE-754 floats, so may result in more
    or fewer steps than expected.

    Examples
    --------
    >>> qvec = GridQVectors(2)
    >>> for i in qvec:
    ...     print(i.q)
    [0. 0. 0.]
    [0. 0. 1.]
    [0. 1. 0.]
    [0. 1. 1.]
    [1. 0. 0.]
    [1. 0. 1.]
    [1. 1. 0.]
    [1. 1. 1.]
    """

    gui_defaults = {
        "grid_u": (
            "RangeConfigurator",
            {
                "label": "Grid U",
                "tooltip": "Set the extent and step of the grid.",
                "valueType": float,
            },
        ),
        "grid_v": (
            "RangeConfigurator",
            {
                "label": "Grid V",
                "tooltip": "Set the extent and step of the grid.",
                "valueType": float,
            },
        ),
        "grid_w": (
            "RangeConfigurator",
            {
                "label": "Grid W",
                "tooltip": "Set the extent and step of the grid.",
                "valueType": float,
            },
        ),
        "origin": (
            "VectorConfigurator",
            {
                "label": "Origin",
                "valueType": float,
                "notNull": False,
                "default": [0, 0, 0],
                "tooltip": "Set the origin of the grid",
            },
        ),
        "hkl": (
            "BooleanConfigurator",
            {
                "label": "In reciprocal lattice",
                "tooltip": "Whether parameters are defined in the basis of the reciprocal lattice or absolute HKL coordinates.",
            },
        ),
    }

    def __init__(
        self,
        ranges: GridSpec,
        origin: ThreeVector = [0, 0, 0],
        *,
        lattice: Optional[UnitCell] = None,
        **kwargs,
    ):
        self.ranges = self._normalise_ranges(ranges)

        if not isinstance(self.ranges, np.ndarray) or self.ranges.shape != (3, 3):
            raise ValueError("`ranges` must be specified for each dimension.")

        self.origin = np.array(origin)

        super().__init__(lattice=lattice, **kwargs)

        if self.hkl:
            self.origin = np.dot(lattice.inverse, self.origin)

        self.generators = [
            self._frange(start + origin, stop + origin, step)
            for start, stop, step, origin in zip(
                self.lower, self.upper, self.step, self.origin
            )
        ]

    @staticmethod
    def _normalise_ranges(ranges: ArrayLike) -> NDArray[float]:
        """Normalise ranges to 3x3 array.

        Parameters
        ----------
        ranges : ArrayLike
            Ranges to standardise.

        Results
        -------
        ndarray[float]
            Ranges as 3x3 start-stop-step in x,y,z.
        """
        if isinstance(ranges, range):
            ranges = GridQVectors.range_to_startstopstep(ranges)
        elif isinstance(ranges, Sequence):
            ranges = [
                r
                if not isinstance(r, range)
                else GridQVectors.range_to_startstopstep(r)
                for r in ranges
            ]

        ranges = np.atleast_2d(np.array(ranges))

        if ranges.shape == (1, 1):  # Stop
            return np.tile([0.0, ranges.item(), 1.0], (3, 1))
        if ranges.shape == (1, 2) or ranges.shape == (2, 1):  # Single start, stop
            return np.tile(np.append(ranges, 1), (3, 1))
        if ranges.shape == (1, 3):  # Single Start, stop, step
            return np.tile(ranges, (3, 1))
        if ranges.shape == (3, 1):  # Single Start, stop, step
            return np.tile(ranges.T, (3, 1))
        if ranges.shape == (3, 2):  # Start, stops
            return np.concatenate((ranges, np.ones((3, 1))), axis=1)

        return ranges

    @property
    def extents(self) -> NDArray[float]:
        """Limits of generation.

        Returns
        -------
        NDArray[float]
            Start-stop of generator.
        """
        return self.ranges[:, :2]

    @property
    def lower(self) -> NDArray[float]:
        """Limits of generation.

        Returns
        -------
        NDArray[float]
            Start of generators.
        """
        return self.ranges[:, 0]

    @property
    def upper(self) -> NDArray[float]:
        """Limits of generation.

        Returns
        -------
        NDArray[float]
            Stop of generators.
        """
        return self.ranges[:, 1]

    @property
    def step(self) -> NDArray[float]:
        """Step of generation.

        Returns
        -------
        NDArray[float]
            Step of generators.
        """
        return self.ranges[:, 2]

    @lower.setter
    def lower(self, value):
        self.ranges[:, 0] = value

    @upper.setter
    def upper(self, value):
        self.ranges[:, 1] = value

    @step.setter
    def step(self, value):
        self.ranges[:, 2] = value

    @property
    def lens(self) -> NDArray[float]:
        """Number of iterations in each dimension.

        Returns
        -------
        NDArray[float]
            Lengths in x, y, z.
        """
        return (self.upper - self.lower) // self.step

    @staticmethod
    def range_to_startstopstep(
        range_: Union[range, slice], limit: int = 10
    ) -> Tuple[int, int, int]:
        """Convert a range or slice to a 3-tuple of start-stop-step.

        Parameters
        ----------
        range_ : range | slice
            Range to convert.
        limit : int
            Max steps for open slice/ranges.

        Returns
        -------
        Tuple[int, int, int]
            Start-stop-step.

        Examples
        --------
        >>> import numpy as np
        >>> GridQVectors.range_to_startstopstep(range(10))
        (0, 10, 1)
        >>> GridQVectors.range_to_startstopstep(np.s_[1:12:3])
        (1, 12, 3)
        >>> GridQVectors.range_to_startstopstep(np.s_[1::0.5])
        (1, 6.0, 0.5)
        """
        return (
            range_.start or 0,
            range_.stop or (range_.start + (limit * (range_.step or 1))),
            range_.step or 1,
        )

    def __len__(self) -> int:
        return np.prod(self.lens)

    def _generate(self, *, lattice: Optional[UnitCell] = None) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice
        constructor = partial(self.qvec_gen, lattice=lattice)

        vectors = map(constructor, cart_prod(*self.generators))

        for qvec in vectors:
            yield qvec

    def reset(self, value: OneOrThree[int] = 0) -> None:
        if isinstance(value, int):
            value = (value, value, value)

        for gen in zip(self.generators, value):
            gen.send(value)

    @staticmethod
    def _frange(start: float, stop: float, step: float) -> Generator[float, int, None]:
        ind = 0

        while start + step * ind < stop:
            new_ind = yield start + step * ind

            ind += 1
            if new_ind is not None:
                ind = new_ind

    @classmethod
    def from_spacing(
        cls,
        spacing: OneOrThree[float],
        extent: OneOrThree[slice | range | Limits],
        **kwargs,
    ):
        """Generate grid from spacing and extents.

        Parameters
        ----------
        spacing : OneOrThree[float]
            Spacing in Q between each point.
        extent : OneOrThree[slice | range | Limits]
            Upper/lower limits for grid.

        Raises
        ------
        ValueError
            If ``range`` specified (normal constructor only).

        Examples
        --------
        >>> qvec = GridQVectors.from_spacing(0.5, (0, 1))
        >>> for i in qvec:
        ...     print(i.q)
        [0. 0. 0.]
        [0.  0.  0.5]
        [0.  0.5 0. ]
        [0.  0.5 0.5]
        [0.5 0.  0. ]
        [0.5 0.  0.5]
        [0.5 0.5 0. ]
        [0.5 0.5 0.5]
        """
        if "range" in kwargs:
            raise ValueError("Cannot pass ``range`` and ``spacing`` simultaneously")

        if isinstance(spacing, float):
            spacing = (spacing,) * 3

        if isinstance(extent, (range, slice)):
            extent = ((extent.start, extent.stop),) * 3
        elif len(extent) == 2:
            extent = (extent,) * 3

        ranges = tuple(
            [start, stop, step] for (start, stop), step in zip(extent, spacing)
        )

        return cls(ranges, **kwargs)
