import itertools
from itertools import product as cart_prod
from math import ceil
from typing import Optional, Union

import numpy as np
from MDANSE.Framework.NewQVectors.QVector import (
    QVecGen,
    QVectorData,
    QVectorGenerator,
    ThreeVector,
)
from MDANSE.Mathematics.Geometry import random_points_on_circle, random_points_on_sphere
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from numpy.typing import ArrayLike


class SphericalQVectors(QVectorGenerator):
    """Generate **Q**-Vectors on the surface of a sphere.

    Parameters
    ----------
    radius : float
        Radius of sphere on which to generate **Q**-vectors.
    centre : ThreeVector
        Origin of sphere.
    seed : Optional[int]
        Random seed for generation of points.
    hkl : bool
        Whether coordinates are specified in reciprocal lattice units
        rather than absolute units.
    lattice : Optional[UnitCell]
        Lattice to use for HKL specification.

    Raises
    ------
    ValueError
        If ``hkl`` requested without lattice.

        If ``centre`` is not a 3-vector.

    Examples
    --------
    >>> vecs = SphericalQVectors(1., seed=3)
    >>> for i,_ in zip(vecs, range(3)):
    ...     print(i)
    QVectorData(q=array([ 0.7300745 ,  0.43579397, -0.52637899]), mod_q=1.0, hkl=None, hkl_exact=None)
    QVectorData(q=array([ 0.31231874, -0.93565731,  0.16432407]), mod_q=1.0, hkl=None, hkl_exact=None)
    QVectorData(q=array([ 0.82268718,  0.55253758, -0.13374612]), mod_q=0.9999999999999999, hkl=None, hkl_exact=None)
    """

    gui_defaults = {
        "radius": (
            "FloatConfigurator",
            {
                "label": "Radius",
                "default": 1.0,
                "mini": 1e-9,
                "tooltip": "Radius of sphere.",
            },
        ),
        "centre": (
            "VectorConfigurator",
            {
                "label": "Centre",
                "valueType": float,
                "notNull": False,
                "default": [0, 0, 0],
            },
        ),
        "seed": (
            "IntegerConfigurator",
            {"label": "Random Seed", "tooltip": "Random seed for sampling."},
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
        radius: float,
        centre: ThreeVector = np.array([0.0, 0.0, 0.0]),
        *,
        seed: Optional[int] = None,
        lattice: Optional[UnitCell] = None,
        **kwargs,
    ):
        self.centre = np.array(centre, dtype=float)

        if self.centre.shape != (3,):
            raise ValueError(f"`centre` ({self.centre.shape}) must be 3-vector.")

        self.radius = radius

        self.rng = np.random.default_rng(seed=seed)
        self.seed = self.rng._bit_generator.seed_seq.entropy

        super().__init__(lattice=lattice, **kwargs)

        if self.hkl:
            self.centre = np.dot(lattice.inverse, self.centre)
            self.radius *= np.linalg.norm(lattice.inverse)

    def __len__(self):
        return np.inf

    def generate_n(self, n: int, lattice: Optional[UnitCell] = None) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice

        return (
            QVectorData(qpt + self.centre, lattice)
            for qpt in random_points_on_sphere(
                radius=self.radius, nPoints=n, rng=self.rng
            )
        )

    def generate_shell(
        self,
        radius: Union[float, tuple[float, float]],
        width: Optional[float] = 0.0,
        *,
        lattice: Optional[UnitCell] = None,
    ) -> QVecGen:
        if isinstance(radius, tuple) and width:
            raise ValueError("Specified width as both tuple and arg.")

        if isinstance(radius, tuple):
            width = radius[1] - radius[0]
            radius = radius[1] - radius[0] / 2

        fac = (
            (self.rng.uniform(-width, width) for _ in itertools.count())
            if width
            else itertools.repeat(0.0)
        )

        lattice = lattice if lattice is not None else self.lattice

        while True:
            yield QVectorData(
                random_points_on_sphere(radius, 1, rng=self.rng).T[0]
                + self.centre
                + next(fac),
                lattice,
            )


    def generate(
        self,
        *,
        lattice: Optional[UnitCell] = None,
    ) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice

        while True:
            yield QVectorData(
                random_points_on_sphere(self.radius, 1, rng=self.rng).T[0]
                + self.centre,
                lattice,
            )

    def _generate(self, *, lattice: Optional[UnitCell] = None) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice

        while True:
            yield QVectorData(
                random_points_on_sphere(self.radius, 1, rng=self.rng).T[0]
                + self.centre,
                lattice,
            )

    def reset(self, value: Optional[int] = None):
        if value is None:
            self.rng = np.random.default_rng(self.seed)
        else:
            self.rng = np.random.default_rng(value)


class LatticeSphericalQVectors(QVectorGenerator):
    """Generate q-vectors commensurate with lattice within sphere.

    Parameters
    ----------
    lattice : UnitCell
        Lattice in which to generate Q-Vectors.
    q_radius : float
        Radius in which to generate vectors.
    centre : ThreeVector
        Origin with which to compare data.
    hkl : bool
        Whether ``centre`` is specified in reciprocal lattice units
        rather than absolute units.

    Notes
    -----
    Radius of sphere (``q_radius``) in absolute inverse length units.

    Raises
    ------
    ValueError
        If centre is not a valid 3-vector.

    Examples
    --------
    >>> import numpy as np
    >>> from MDANSE.MolecularDynamics.UnitCell import UnitCell
    >>> latt = UnitCell(np.diag([5., 5., 5.]))
    >>> vecs = LatticeSphericalQVectors(latt, 2.)
    >>> for i in vecs[3]:
    ...     print(i)
    QVectorData(q=array([-1.8, -0.8, -0.2]), mod_q=1.9798989873223332, hkl=array([-9., -4., -1.]), hkl_exact=array([-9., -4., -1.]))
    QVectorData(q=array([-1.8, -0.8,  0. ]), mod_q=1.969771560359221, hkl=array([-9., -4.,  0.]), hkl_exact=array([-9., -4.,  0.]))
    QVectorData(q=array([-1.8, -0.8,  0.2]), mod_q=1.9798989873223332, hkl=array([-9., -4.,  1.]), hkl_exact=array([-9., -4.,  1.]))
    """

    gui_defaults = {
        "q_radius": (
            "FloatConfigurator",
            {
                "label": "Q Radius",
                "default": 1.0,
                "mini": 1e-9,
                "tooltip": "Radius of sphere in space.",
            },
        ),
        "hkl": (
            "BooleanConfigurator",
            {
                "label": "In reciprocal lattice",
                "tooltip": "Whether `centre` is defined in the basis of the reciprocal lattice or absolute HKL coordinates.",
            },
        ),
        # "_centre": (
        #     "VectorConfigurator",
        #     {
        #         "label": "Centre",
        #         "valueType": float,
        #         "notNull": False,
        #         "default": [0, 0, 0],
        #     },
        # ),
    }

    def __init__(
        self,
        lattice: UnitCell,
        q_radius: float,
        _centre: ThreeVector = [0, 0, 0],
        **kwargs,
    ):
        self.centre = np.array(_centre, dtype=float)
        self.radius = q_radius

        if self.centre.shape != (3,):
            raise ValueError(f"`centre` ({self.centre.shape}) must be 3-vector.")

        if not np.allclose(self.centre, [0, 0, 0]):
            raise NotImplementedError("Arbitrary centre not currently implemented.")

        super().__init__(lattice=lattice, **kwargs)

        if self.hkl:
            self.centre = np.dot(lattice.inverse, self.centre)

    def __len_hint__(self) -> int:
        return (2 * ceil(self.q_radius) + 1) ** 3 - self._ind

    def generate_shell(
        self,
        radius: Union[float, tuple[float, float]],
        width: Optional[float] = 0.0,
        *,
        lattice: Optional[UnitCell] = None,
    ) -> QVecGen:
        if isinstance(radius, tuple) and width:
            raise ValueError("Specified width as both tuple and arg.")

        if isinstance(radius, float):
            radius = (radius - width, radius + width)

        lattice = lattice if lattice is not None else self.lattice

        hkl_radius = (
            ceil(radius[1] / np.linalg.norm(e)) + 1 for e in lattice.inverse
        )

        extent = (range(-hkl, hkl + 1) for hkl in hkl_radius)

        vectors = (
            np.dot(lattice.inverse, np.array(coords)) for coords in cart_prod(*extent)
        )

        vectors = filter(
            lambda vec: self.radius[0]
            <= np.linalg.norm(vec - self.centre)
            <= self.radius[1],
            vectors,
        )

        for self._ind, vec in enumerate(vectors):
            yield QVectorData(vec + self.centre, lattice)

    def _generate(self, lattice: Optional[UnitCell] = None) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice

        hkl_radius = (
            ceil(self.radius / np.linalg.norm(e)) + 1
            for e in lattice.inverse
        )

        extent = (range(-hkl, hkl + 1) for hkl in hkl_radius)
        vectors = (
            np.dot(lattice.inverse, np.array(coords)) for coords in cart_prod(*extent)
        )

        vectors = filter(
            lambda vec: np.linalg.norm(vec - self.centre) <= self.radius, vectors
        )

        for self._ind, vec in enumerate(vectors):
            yield QVectorData(vec + self.centre, lattice)

    def reset(self, value: int = 0):
        raise ValueError("Cannot reset generator")


class CircularQVectors(QVectorGenerator):
    """Generate **Q**-vectors on a circle or annulus aligned with an axis.

    Parameters
    ----------
    radius : float
        Radius of circle to generate.
    axis : ThreeVector
        Pricipal axis of circle.
    centre : ThreeVector
        Centre of circle in Q-space.
    seed : Optional[int]
        Random seed for generation.
    lattice : Optional[UnitCell]
        Lattice to use for generation.

    Raises
    ------
    ValueError
        If `axis` or `centre` are not 3-vectors.

    Examples
    --------
    >>> vecs = CircularQVectors(2., [1, 0, 0], seed=3)
    >>> for i in vecs[3]:
    ...     print(i)
    QVectorData(q=array([ 0.        , -1.31580351,  1.50620753]), mod_q=2.0, hkl=None, hkl_exact=None)
    QVectorData(q=array([ 0.        , -1.97339328, -0.32514452]), mod_q=2.0, hkl=None, hkl_exact=None)
    QVectorData(q=array([ 0.        , -1.6466193 ,  1.13518495]), mod_q=2.0, hkl=None, hkl_exact=None)
    """

    gui_defaults = {
        "radius": (
            "FloatConfigurator",
            {
                "label": "Radius",
                "mini": 0.01,
                "default": 1.0,
                "tooltip": "Radius of disc in which vectors are generated.",
            },
        ),
        "axis": (
            "VectorConfigurator",
            {
                "label": "Axis",
                "valueType": float,
                "notNull": True,
                "default": [1, 0, 0],
                "tooltip": "Principal axis of disc to generate vectors on.",
            },
        ),
        "centre": (
            "VectorConfigurator",
            {
                "label": "Centre",
                "valueType": float,
                "default": [0, 0, 0],
                "tooltip": "Origin of disc.",
            },
        ),
        "seed": (
            "IntegerConfigurator",
            {"label": "Random Seed", "tooltip": "Random seed for sampling."},
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
        radius: float,
        axis: ThreeVector,
        centre: ThreeVector = np.array([0.0, 0.0, 0.0]),
        *,
        seed: Optional[int] = None,
        lattice: Optional[UnitCell] = None,
        **kwargs,
    ):
        self.centre = np.array(centre, dtype=float)
        self.axis = np.array(axis, dtype=float)

        if self.axis.shape != (3,):
            raise ValueError(f"`axis` ({self.axis.shape}) must be 3-vector.")
        if self.centre.shape != (3,):
            raise ValueError(f"`centre` ({self.centre.shape}) must be 3-vector.")

        self.radius = radius

        self.rng = np.random.default_rng(seed=seed)
        self.seed = self.rng._bit_generator.seed_seq.entropy

        super().__init__(lattice=lattice, **kwargs)

        if self.hkl:
            self.centre = np.dot(lattice.inverse, self.centre)
            self.axis = np.dot(lattice.inverse, self.axis)
            self.radius *= np.linalg.norm(lattice.inverse)

    def __len__(self) -> int:
        return np.inf

    def generate_shell(
        self,
        radius: Union[float, tuple[float, float]],
        width: Optional[float] = 0.0,
        *,
        lattice: Optional[UnitCell] = None,
    ) -> QVecGen:
        if isinstance(radius, tuple) and width:
            raise ValueError("Specified width as both tuple and arg.")

        if isinstance(radius, tuple):
            width = radius[1] - radius[0]
            radius = radius[1] - radius[0] / 2

        fac = (
            (self.rng.uniform(-width, width) for _ in itertools.count())
            if width
            else itertools.repeat(0.0)
        )

        lattice = lattice if lattice is not None else self.lattice

        while True:
            yield QVectorData(
                random_points_on_circle(
                    self.axis, radius + next(fac), 1, rng=self.rng
                ).T[0]
                + self.centre,
                lattice,
            )

    def generate(
        self,
        *,
        lattice: Optional[UnitCell] = None,
    ) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice

        while True:
            yield QVectorData(
                random_points_on_circle(self.axis, self.radius, 1, rng=self.rng).T[0]
                + self.centre,
                lattice,
            )

    def _generate(self, *, lattice: Optional[UnitCell] = None) -> QVecGen:
        lattice = lattice if lattice is not None else self.lattice

        while True:
            yield QVectorData(
                random_points_on_circle(self.axis, self.radius, 1, rng=self.rng).T[0]
                + self.centre,
                lattice,
            )

    def reset(self, value: Optional[int] = None) -> None:
        if value is None:
            self.rng = np.random.default_rng(self.seed)
        else:
            self.rng = np.random.default_rng(value)
