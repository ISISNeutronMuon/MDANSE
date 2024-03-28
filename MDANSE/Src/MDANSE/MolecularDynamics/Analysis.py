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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now

import numpy as np
from numpy.typing import NDArray

from MDANSE.Core.Error import Error
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.Mathematics.Signal import correlation


class AnalysisError(Error):
    pass


def mean_square_deviation(
    coords1: np.ndarray,
    coords2: np.ndarray,
    masses: np.ndarray = None,
    root: bool = False,
) -> float:
    """
    Computes the mean square deviation between two sets of coordinates using the following function:
    .. math:: \\frac{\\sum_{i=0} ^{n} ((\\sum_{x=1} ^{3} (coords1_{i,x} - coords2_{i,x})^2) * m_i)}{\\sum_{i=0} ^{n} m_i}
    where n is the number of particles (i.e. the length of the provided arrays), coords1 and coords2 are the provided
    coordinate arrays, so :math: `coords1_{i,x}` is equivalent to coords[i, x] where i is atom index and x is axis, and
    m is the provided array of masses, or an array of ones if None is passed in.

    :param coords1: the first set of n coordinates.
    :type coords1: (n,3) numpy array

    :param coords2: the second set of n coordinates.
    :type coords2: (n,3) numpy array

    :param masses: the n input masses. If None the center of gravity is computed.
    :type masses: n-numpy array

    :param root: if True, return the square root of MSD, i.e. the root-mean-square deviation
    :type root: bool

    :return: the mean square deviation.
    :rtype: float
    """

    if coords1.shape != coords2.shape:
        raise AnalysisError("The input coordinates shapes do not match")

    if masses is None:
        masses = np.ones((coords1.shape[0]), dtype=np.float64)

    rmsd = np.sum(np.sum((coords1 - coords2) ** 2, axis=1) * masses) / np.sum(masses)

    if root:
        rmsd = np.sqrt(rmsd)

    return rmsd


def mean_square_displacement(coords: np.ndarray) -> NDArray[np.float64]:
    """
    Computes the mean square displacement of a set of coordinates using the MSD algorithm described in Kneller et al.,
    Com. Phys. Com., 1995.

    :param coords: the set of n coordinates.
    :type coords: (n,3) numpy array

    :return: the mean square displacement.
    :rtype: np.ndarray
    """

    dsq = np.add.reduce(coords**2, 1)

    # sum_dsq1 is the cumulative sum of dsq
    sum_dsq1 = np.add.accumulate(dsq)

    # sum_dsq1 is the reversed cumulative sum of dsq
    sum_dsq2 = np.add.accumulate(dsq[::-1])

    # sumsq refers to SUMSQ in the published algorithm
    sumsq = 2.0 * sum_dsq1[-1]

    # this line refers to the instruction SUMSQ <-- SUMSQ - DSQ(m-1) - DSQ(N - m) of the published algorithm
    # In this case, msd is an array because the instruction is computed for each m ranging from 0 to len(traj) - 1
    # So, this single instruction is performing the loop in the published algorithm
    Saabb = (
        sumsq
        - np.concatenate(([0.0], sum_dsq1[:-1]))
        - np.concatenate(([0.0], sum_dsq2[:-1]))
    )

    # Saabb refers to SAA+BB/(N-m) in the published algorithm
    # Sab refers to SAB(m)/(N-m) in the published algorithm
    Saabb = Saabb / (len(dsq) - np.arange(len(dsq)))
    Sab = 2.0 * correlation(coords, axis=0, sumOverAxis=1)

    # The atomic MSD.
    msd = Saabb - Sab

    return msd


def mean_square_fluctuation(coords: np.ndarray, root: bool = False) -> float:
    """
    Computes the mean-square fluctuation, or the root-mean-square fluctuation if root is set to True. The following
    equation is used:
    .. math:: MSF = \\frac{\\sum_{i=0} ^{n} \\sum_{x=1} ^{3}(coords_{i,x} - \\frac{\\sum_{j=0} ^{n}coords_{j,x}}{n})^2}{n}
    where n is the number of particles in the system and coords are is the array of coordinates.

    :param coords: the coordinates whose MSF is to be calculated
    :type coords: np.ndarray

    :param root: boolean value determining whether the result should be a square root or not
    :type root: bool

    :return: the mean-square fluctuation
    :rtype: float
    """
    msf = np.average(np.sum((coords - np.average(coords, axis=0)) ** 2, axis=1))

    if root:
        msf = np.sqrt(msf)

    return msf


def radius_of_gyration(
    coords: np.ndarray, masses: np.ndarray = None, root: bool = False
) -> float:
    """
    Computes the radius of gyration for a set of coordinates and their corresponding masses. If no masses are provided,
    all masses are set to 1, in which case the ROG is equivalent to the centre of gravity. The following equation is
    used:
    .. math:: ROG = \\frac{\\sum_{i=0} ^{n}((\\sum_{x=1} ^{3} (coords_{i,x} - com_x)^2) * m_i)}{\\sum_{i=0} ^{n} m_i}
    where n is the number of particles (i.e. the length of the arrays), x is the axis (x, y, or z), coords is the
    provided coordinate array, com are the coordinates of the centre of mass as calculated by
    :func: `MDANSE.Mathematics.Geometry.center_of_mass`, and m is the provided array of masses.

    :param coords: the set of n coordinates.
    :type coords: (n,3) numpy array

    :param masses: the n input masses. If None the center of gravity is computed.
    :type masses: n-numpy array

    :param root: if True, return the square root of the radius of gyration.
    :type root: bool

    :return: the radius of gyration
    :rtype: float
    """

    if masses is None:
        masses = np.ones((coords.shape[0]), dtype=np.float64)

    com = center_of_mass(coords, masses)

    rog = np.sum(np.sum((coords - com) ** 2, axis=1) * masses) / np.sum(masses)

    if root:
        rog = np.sqrt(rog)

    return rog
