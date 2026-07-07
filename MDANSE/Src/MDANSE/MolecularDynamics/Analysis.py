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

from typing import TYPE_CHECKING

import numpy as np
from scipy.signal import correlate

from MDANSE.Mathematics.Geometry import center_of_mass

if TYPE_CHECKING:
    from MDANSE.util_types import FloatArray


class AnalysisError(Exception):
    pass


def mean_square_displacement(coords: FloatArray, n_configs: int) -> FloatArray:
    """Computes the mean square displacement of a set of coordinates
    using the MSD algorithm described in Kneller et al., Com. Phys. Com., 1995.

    Parameters
    ----------
    coords : FloatArray
        Coordinates used to calculate MSD.
    n_configs : int
        Size of the window used to correlated positions.

    Returns
    -------
    FloatArray
        An array of the MSD.
    """
    r2 = coords * coords
    window = np.ones((n_configs, 3))
    r2t = correlate(r2, window, mode="valid").T[0] / n_configs
    rtr0 = correlate(coords, coords[:n_configs], mode="valid").T[0] / n_configs
    msd = r2t[0] + r2t - 2 * rtr0
    return msd


def mean_square_fluctuation(coords: FloatArray, root: bool = False) -> float:
    """Computes the mean-square fluctuation, or the root-mean-square fluctuation if root is set to True. The following
    equation is used:
    .. math:: MSF = \\frac{\\sum_{i=0} ^{n} \\sum_{x=1} ^{3}(coords_{i,x} - \\frac{\\sum_{j=0} ^{n}coords_{j,x}}{n})^2}{n}
    where n is the number of particles in the system and coords are is the array of coordinates.

    Parameters
    ----------
    coords : FloatArray
        the coordinates whose MSF is to be calculated
    root : bool
        boolean value determining whether the result should be a square root or not

    Returns
    -------
    float
        the mean-square fluctuation

    """
    msf = np.average(np.sum((coords - np.average(coords, axis=0)) ** 2, axis=1))

    if root:
        msf = np.sqrt(msf)

    return float(msf)


def radius_of_gyration(
    coords: FloatArray,
    masses: FloatArray | None = None,
    root: bool = False,
) -> float:
    """Computes the radius of gyration for a set of coordinates and their corresponding masses. If no masses are provided,
    all masses are set to 1, in which case the ROG is equivalent to the centre of gravity. The following equation is
    used:
    .. math:: ROG = \\frac{\\sum_{i=0} ^{n}((\\sum_{x=1} ^{3} (coords_{i,x} - com_x)^2) * m_i)}{\\sum_{i=0} ^{n} m_i}
    where n is the number of particles (i.e. the length of the arrays), x is the axis (x, y, or z), coords is the
    provided coordinate array, com are the coordinates of the centre of mass as calculated by
    :func: `MDANSE.Mathematics.Geometry.center_of_mass`, and m is the provided array of masses.

    Parameters
    ----------
    coords : (n,3) numpy array
        the set of n coordinates.
    masses : (n,) numpy array
        the n input masses. If None the center of gravity is computed.
    root : bool
        if True, return the square root of the radius of gyration.

    Returns
    -------
    float
        the radius of gyration

    """

    if masses is None:
        masses = np.ones((coords.shape[0]), dtype=np.float64)

    com = center_of_mass(coords, masses)

    rog = np.sum(np.sum((coords - com) ** 2, axis=1) * masses) / np.sum(masses)

    if root:
        rog = np.sqrt(rog)

    return rog
