#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Apr 13, 2015

:author: Gael Goret, Eric C. Pellegrini
'''

import matplotlib.ticker

class ScaledLocator(matplotlib.ticker.MaxNLocator):
    """
    Locates regular intervals along an axis scaled by *dx* and shifted by
    *x0*. For example, this would locate minutes on an axis plotted in seconds
    if dx=60.  This differs from MultipleLocator in that an approriate interval
    of dx units will be chosen similar to the default MaxNLocator.
    """
    def __init__(self, dx=1.0, x0=0.0):
        self.dx = dx
        self.x0 = x0
        matplotlib.ticker.MaxNLocator.__init__(self, nbins=9, steps=[1, 2, 5, 10])

    def rescale(self, x):
        return x * self.dx + self.x0
    def inv_rescale(self, x):
        return  (x - self.x0) / self.dx

    def __call__(self): 
        vmin, vmax = self.axis.get_view_interval()
        vmin, vmax = self.rescale(vmin), self.rescale(vmax)
        vmin, vmax = matplotlib.transforms.nonsingular(vmin, vmax, expander = 0.05)
        locs = self.bin_boundaries(vmin, vmax)
        locs = self.inv_rescale(locs)
        prune = self._prune
        if prune=='lower':
            locs = locs[1:]
        elif prune=='upper':
            locs = locs[:-1]
        elif prune=='both':
            locs = locs[1:-1]
        return self.raise_if_exceeds(locs)

class ScaledFormatter(matplotlib.ticker.OldScalarFormatter):
    """Formats tick labels scaled by *dx* and shifted by *x0*."""
    def __init__(self, dx=1.0, x0=0.0, **kwargs):
        self.dx, self.x0 = dx, x0

    def rescale(self, x):
        return x * self.dx + self.x0

    def __call__(self, x, pos=None):
        xmin, xmax = self.axis.get_view_interval()
        xmin, xmax = self.rescale(xmin), self.rescale(xmax)
        d = abs(xmax - xmin)
        x = self.rescale(x)
        s = self.pprint_val(x, d)
        return s
