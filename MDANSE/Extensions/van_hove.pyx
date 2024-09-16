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

import cython
cimport numpy as np
from numpy cimport ndarray


cdef extern from "math.h":
    double floor(double x)
    double ceil(double x)
    double sqrt(double x)


cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)


def van_hove_distinct(
    double[:,:] cell,
    int[:] molindex,
    int[:] symbolindex,
    double[:,:,:] intra,
    double[:,:,:] inter,
    double[:,:] scaleconfig_t0,
    double[:,:] scaleconfig_t1,
    double rmin,
    double dr
):
    """Calculates the distance histogram between the configurations at
    times t0 and t1. Distances are calculated using the minimum image
    convention which are all worked out using the fractional coordinates
    with the unit cell of the configuration at time t1. The function can
    be used to calculate the distinct part of the Van Hove function.

    This function was an generalization of a Pyrex adaptation of a
    FORTRAN implementation made by Miguel Angel Gonzalez (Institut Laue
    Langevin) for the calculation of intra and intermolecular distance
    histograms.

    Parameters
    ----------
    cell : np.ndarray
        The transpose of the direct matrix of the configuration at
        time t1.
    molindex : np.ndarray
        An array which maps atom indexes to molecule indexes.
    symbolindex : np.ndarray
        An array which maps atom indexes to symbol indexes.
    intra : np.ndarray
        An output array to save the distance histogram results of
        intramolecular atom differences.
    inter : np.ndarray
        An output array to save the distance histogram results of
        intermolecular atom differences.
    scaleconfig_t0 : np.ndarray
        The coordinates of the configuration at t0 in fractional
        coordinate in the unit cell of the configuration at time t1.
    scaleconfig_t1 : np.ndarray
        The coordinates of the configuration at t1 in fractional
        coordinate in the unit cell of the configuration at time t1.
    rmin : float
        The minimum distance of the histogram.
    dr : float
        The distances between histogram bins.
    """

    cdef double sdx, sdy, sdz, rx, ry, rz, r
    cdef int i, j, bin, nbins
    nbins = intra.shape[2]

    for i in range(scaleconfig_t0.shape[0] - 1):

        sx = scaleconfig_t0[i,0]
        sy = scaleconfig_t0[i,1]
        sz = scaleconfig_t0[i,2]

        for j in range(i + 1, scaleconfig_t0.shape[0]):

            sdx = scaleconfig_t1[j,0] - sx
            sdy = scaleconfig_t1[j,1] - sy
            sdz = scaleconfig_t1[j,2] - sz

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            rx = sdx*cell[0,0] + sdy*cell[0,1] + sdz*cell[0,2]
            ry = sdx*cell[1,0] + sdy*cell[1,1] + sdz*cell[1,2]
            rz = sdx*cell[2,0] + sdy*cell[2,1] + sdz*cell[2,2]

            r = sqrt(rx*rx + ry*ry + rz*rz)

            bin = <int>((r-rmin)/dr)

            if ((bin < 0) or (bin >= nbins)):
                continue

            if molindex[i] == molindex[j]:
                intra[symbolindex[i],symbolindex[j],bin] += 1.0
            else:
                inter[symbolindex[i],symbolindex[j],bin] += 1.0
