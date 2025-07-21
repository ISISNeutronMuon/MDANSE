import itertools
from typing import Optional, Sequence, Union, overload

import numpy as np
from MDANSE.Framework.NewQVectors.QVector import (
    QVecGen,
    QVectorData,
    QVectorGenerator,
    ThreeVector,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from numpy.typing import ArrayLike


class LinearQVectors(QVectorGenerator):
    """Generate **Q**-Vectors in a linear path from an initial point.

    Parameters
    ----------
    direction : ThreeVector
        Direction to advance.
    q_step : Optional[float]
        Length of each step in direction.

        If ``None`` will default to the magnitude of `direction`.
    q_start : ThreeVector
        Intitial point to start path.
    hkl : bool
        Whether coordinates are expressed in reciprocal lattice units.

    Raises
    ------
    ValueError
        Given ``q_start`` or ``direction`` are not 3-vectors.

    Examples
    --------
    >>> vec = LinearQVectors([1, 0, 0])
    >>> [list(qvec.q) for qvec in vec[3]]
    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]

    Notes
    -----
    Generates an infinite set of Q-Vectors starting from the initial point.
    """

    gui_defaults = {
        "direction": (
            "VectorConfigurator",
            {
                "label": "Direction",
                "valueType": float,
                "notNull": True,
                "default": [1, 0, 0],
                "tooltip": "Direction of vector in space.",
            },
        ),
        "q_step": (
            "OptionalFloatConfigurator",
            {
                "label": "Q Step",
                "mini": 1e-9,
                "tooltip": "Length of step between each vector.",
            },
        ),
        "q_start": (
            "VectorConfigurator",
            {
                "label": "Origin",
                "valueType": float,
                "default": [0, 0, 0],
                "tooltip": "Origin of line in space.",
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
        direction: ThreeVector,
        q_step: Optional[float] = None,
        q_start: ThreeVector = np.array([0.0, 0.0, 0.0]),
        *,
        lattice: Optional[UnitCell] = None,
        **kwargs,
    ):
        super().__init__(lattice=lattice, **kwargs)

        self.direction = np.array(direction, dtype=float)

        self.q_start = np.array(q_start, dtype=float)

        if not (self.q_start.shape == self.direction.shape == (3,)):
            raise ValueError(
                f"`q_start` ({self.q_start.shape}) "
                f"and `direction`  ({self.direction.shape}) must be 3-vectors."
            )

        dist = np.linalg.norm(self.direction)

        self.q_step = q_step if q_step is not None else dist

        self.direction /= dist

        if self.hkl:
            self.direction = np.dot(lattice.inverse, self.direction)
            dir_scale = np.linalg.norm(self.direction)

            self.q_step *= dir_scale
            self.direction /= dir_scale

    def _generate(self, *, lattice: Optional[UnitCell] = None) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice

        while True:
            qvec = QVectorData(
                self.q_start + (self.direction * self.q_step * self._ind), lattice
            )
            ind = yield qvec

            self._ind += 1
            if ind is not None:
                self._ind = ind

    def reset(self, value: int = 0):
        super().reset(value)

    def __len__(self) -> int:
        return np.inf


class PathSegmentQVectors(LinearQVectors):
    """Linear vector between two points.

    Parameters
    ----------
    q_start : ThreeVector
        Start point of path.
    q_end : ThreeVector
        End point of path.
    q_step : Optional[float]
        Length of step.
    steps : Optional[int]
        Number of steps to divide into.
    include_end : bool
        Include the end of the path as a step.

    Raises
    ------
    ValueError
        If both ``steps`` and ``q_step`` are present.

    Notes
    -----
    Only one of ``q_step`` and ``steps`` may be present.

    Examples
    --------
    >>> vec = PathSegmentQVectors([0, 0, 0], [1, 1, 1], steps=2)
    >>> for qvec in vec.generate():
    ...     print(qvec.q)
    [0. 0. 0.]
    [0.5 0.5 0.5]
    >>> vec = PathSegmentQVectors([0, 0, 0], [1, 0, 0], q_step=0.5, include_end=True)
    >>> for qvec in vec.generate():
    ...     print(qvec.q)
    [0. 0. 0.]
    [0.5 0.  0. ]
    [1. 0. 0.]
    """

    gui_defaults = {
        "q_start": (
            "VectorConfigurator",
            {
                "label": "Q Start",
                "valueType": float,
                "default": [0, 0, 0],
                "tooltip": "Origin of line-segment in space.",
            },
        ),
        "q_end": (
            "VectorConfigurator",
            {
                "label": "Q End",
                "valueType": float,
                "default": [1, 0, 0],
                "tooltip": "End-point of line-segment in space.",
            },
        ),
        "q_step": (
            "OptionalFloatConfigurator",
            {
                "label": "Q Step",
                "mini": 1e-9,
                "tooltip": "Length of steps between start- and end-points.\n\nMutually exclusive with `steps`.",
            },
        ),
        "steps": (
            "OptionalFloatConfigurator",
            {
                "label": "Steps",
                "mini": 1,
                "tooltip": "Number of steps betwene start- and end-points.\n\nMutually exclusive with `Q Step`",
            },
        ),
        "include_end": (
            "BooleanConfigurator",
            {
                "label": "Include end-point.",
                "tooltip": "Whether range is to be considered in- or exclusive.",
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

    @overload
    def __init__(
        self,
        q_start: ThreeVector,
        q_end: ThreeVector,
        *,
        q_step: float,
        include_end: bool,
        **kwargs,
    ): ...
    @overload
    def __init__(
        self,
        q_start: ThreeVector,
        q_end: ThreeVector,
        *,
        steps: int,
        include_end: bool,
        **kwargs,
    ): ...

    def __init__(
        self,
        q_start: ThreeVector = [0, 0, 0],
        q_end: ThreeVector = [1, 0, 0],
        *,
        q_step: Optional[float] = None,
        steps: Optional[int] = None,
        include_end: bool = False,
        **kwargs,
    ):
        if (steps is None and q_step is None) or (
            steps is not None and q_step is not None
        ):
            raise ValueError("One of steps and q_step must be defined")

        q_end = np.array(q_end, dtype=float)
        q_start = np.array(q_start, dtype=float)

        direction = q_end - q_start
        dist = np.linalg.norm(direction)

        if steps is not None:
            q_step = dist / (steps - include_end)

        super().__init__(direction, q_step, q_start, **kwargs)

        self.dist = dist
        self.steps = (
            steps if steps is not None else int(dist // self.q_step) + include_end
        )

    def __len__(self) -> int:
        return self.steps

    def _generate(self, *, lattice: Optional[UnitCell] = None) -> QVecGen:
        return itertools.islice(super()._generate(lattice=lattice), self.steps)


class LatticeLinearQVectors(LinearQVectors):
    """Generate Q vectors with spacing defined in :math:`hkl`.

    This differs from :class:`LinearQVectors` by rescaling
    steps to be in reciprocal lattice units.

    Parameters
    ----------
    lattice : UnitCell
        Lattice in which to generate Q-Vectors.
    direction : ThreeVector
        Vector over which to iterate.
    q_step : float
        Length of step in Q, if not specified will
        be derived from the magnitude of ``direction``.
    q_start : ThreeVector
        Origin point for line.

    Examples
    --------
    >>> import numpy as np
    >>> from MDANSE.MolecularDynamics.UnitCell import UnitCell
    >>> lattice = UnitCell(np.diag([5., 5., 5.]))
    >>> vec = LatticeLinearQVectors(lattice, [1, 0, 0])
    >>> for qvec in vec[3]:
    ...     print(qvec)
    QVectorData(q=array([0., 0., 0.]), mod_q=0.0, hkl=array([0., 0., 0.]), hkl_exact=array([0., 0., 0.]))
    QVectorData(q=array([0.2, 0. , 0. ]), mod_q=0.2, hkl=array([1., 0., 0.]), hkl_exact=array([1., 0., 0.]))
    QVectorData(q=array([0.4, 0. , 0. ]), mod_q=0.4, hkl=array([2., 0., 0.]), hkl_exact=array([2., 0., 0.]))
    """

    gui_defaults = {
        "direction": (
            "VectorConfigurator",
            {
                "label": "Direction",
                "valueType": float,
                "notNull": True,
                "default": [1, 0, 0],
                "tooltip": "Direction of line in space.",
            },
        ),
        "q_step": (
            "OptionalFloatConfigurator",
            {
                "label": "Q Step",
                "mini": 1e-9,
                "tooltip": "Length of each step.\n\nIf unspecified, the magnitude of `direction` will be used.",
            },
        ),
        "q_start": (
            "VectorConfigurator",
            {
                "label": "Q Start",
                "valueType": float,
                "default": [0, 0, 0],
                "tooltip": "Origin of line in space.",
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
        lattice: UnitCell,
        direction: ThreeVector,
        q_step: float = None,
        q_start: ThreeVector = np.array([0.0, 0.0, 0.0]),
        **kwargs,
    ):
        super().__init__(
            direction, q_step, q_start, lattice=lattice, hkl=True, **kwargs
        )


class PathLinearQVectors(QVectorGenerator):
    """Generate **q**-vectors along a path through **k**-space.

    Parameters
    ----------
    *k_pts : ArrayLike
        Sequence of points on path.
    q_step : Optional[float]
        Length of step.
    steps : Union[None, int, Sequence[int]]
        Number of steps along each path.

    Notes
    -----
    Only one of ``q_step`` and ``steps`` may be present.

    ``steps`` is not recommended as this may lead to irregular spacing
    for paths which are not evenly spaced.

    Examples
    --------
    >>> vec = PathLinearQVectors([[0, 0, 0], [1, 0, 0], [1, 1, 0]], q_step=0.5)
    >>> for qvec in vec.generate():
    ...     print(qvec.q)
    [0. 0. 0.]
    [0.5 0.  0. ]
    [1. 0. 0.]
    [1.  0.5 0. ]
    [1. 1. 0.]
    >>> vec = PathLinearQVectors([[0, 0, 0], [1, 0, 0], [1, 1, 0]], steps=2)
    >>> for qvec in vec.generate():
    ...     print(qvec.q)
    [0. 0. 0.]
    [0.5 0.  0. ]
    [1. 0. 0.]
    [1.  0.5 0. ]
    [1. 1. 0.]

    See Also
    --------
    PathSegmentQVectors : Implementation of generator.
    """

    gui_defaults = {
        "k_pts": (
            "VectorList",
            {
                "label": "K Points",
                "tooltip": "Path segment end-points on the path that the q-vectors will follow.",
                "n_rows": 3,
                "n_dims": 3,
                "wildcard": "(*) All files;;",
            },
        ),
        "q_step": (
            "OptionalFloatConfigurator",
            {
                "label": "Q Step",
                "tooltip": "Fixed step length between points.",
            },
        ),
        "steps": (
            "StringConfigurator",
            {
                "label": "Number of steps.",
                "tooltip": "Number of steps in each segment.",
            },
        ),
        "include_end": (
            "BooleanConfigurator",
            {
                "label": "Include end",
                "tooltip": "Include end-point of steps",
            },
        ),
        "hkl": (
            "BooleanConfigurator",
            {
                "label": "In reciprocal lattice",
                "tooltip": (
                    "Whether parameters are defined in the basis "
                    "of the reciprocal lattice or "
                    "absolute HKL coordinates."
                ),
            },
        ),
    }

    @overload
    def __init__(
        self, k_pts: ArrayLike, q_step: float, include_end: bool, **kwargs
    ): ...

    @overload
    def __init__(
        self, k_pts: ArrayLike, q_step: float, include_end: bool, **kwargs
    ): ...

    def __init__(
        self,
        k_pts: ArrayLike,
        *,
        q_step: Optional[float] = None,
        steps: Union[None, int, Sequence[int]] = None,
        include_end: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.k_pts = np.array(k_pts)
        self.n_segments = len(self.k_pts)
        n_paths = self.n_segments - 1

        if isinstance(steps, int):
            steps = [steps] * n_paths
            if include_end:
                steps[-1] += 1
        elif steps is None:
            steps = [None] * n_paths

        is_end = [False] * n_paths
        is_end[-1] = include_end

        if len(steps) != n_paths:
            raise ValueError(
                f"Number of specified steps ({len(steps)}) "
                f"must match number of paths ({n_paths})."
            )

        self.generators = tuple(
            PathSegmentQVectors(
                q_start, q_stop, q_step=q_step, steps=n_step, include_end=end, **kwargs
            )
            for end, (q_start, q_stop), n_step in zip(
                is_end, itertools.pairwise(self.k_pts), steps
            )
        )

    def _generate(self, *, lattice: Optional[UnitCell] = None) -> QVecGen:
        for generator in self.generators:
            yield from generator._generate(lattice=lattice)

    def reset(self, value: int = 0):
        if value != 0:
            raise ValueError("Can only reset vector generator.")

        for generator in self.generators:
            generator.reset()

    def __len__(self) -> int:
        return sum(len(generator) for generator in self.generators)
