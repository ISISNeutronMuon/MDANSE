# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/PlotterTicker.py
# @brief     Implements module/class/test PlotterTicker
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import matplotlib.ticker

class ScaledLocator(matplotlib.ticker.MaxNLocator):
    """
    Locates regular intervals along an axis scaled by *dx* and shifted by
    *x0*. For example, this would locate minutes on an axis plotted in seconds
    if dx=60.  This differs from MultipleLocator in that an approriate interval
    of dx units will be chosen similar to the default MaxNLocator.
    
    see https://stackoverflow.com/questions/9451395/customize-x-axis-in-matplotlib
    """
    def __init__(self, dx=1.0, x0=0.0):
        self.dx = dx
        self.x0 = x0
        matplotlib.ticker.MaxNLocator.__init__(self, nbins=9, steps=[1, 2, 5, 10])

    def rescale(self, x):
        return x * self.dx + self.x0
    def inv_rescale(self, x):
        return  (x - self.x0) / self.dx

    #def __call__(self): 
    #    vmin, vmax = self.axis.get_view_interval()
    #    vmin, vmax = self.rescale(vmin), self.rescale(vmax)
    #    vmin, vmax = matplotlib.transforms.nonsingular(vmin, vmax, expander = 0.05)
    #    locs = self.bin_boundaries(vmin, vmax)
    #    locs = self.inv_rescale(locs)
    #    prune = self._prune
    #    if prune=='lower':
    #        locs = locs[1:]
    #    elif prune=='upper':
    #        locs = locs[:-1]
    #    elif prune=='both':
    #        locs = locs[1:-1]
    #    return self.raise_if_exceeds(locs)

class ScaledFormatter(matplotlib.ticker.ScalarFormatter):
    """Formats tick labels scaled by *dx* and shifted by *x0*."""
    def __init__(self, dx=1.0, x0=0.0, **kwargs):
        super(ScaledFormatter,self).__init__(**kwargs)
        self.dx, self.x0 = dx, x0

    def rescale(self, x):
        return x * self.dx + self.x0

    def pprint_val(self, x, d):
        """
        Formats the value `x` based on the size of the axis range `d`.
        """
        # If the number is not too big and it's an int, format it as an int.
        if abs(x) < 1e4 and x == int(x):
            return '%d' % x

        if d < 1e-2:
            fmt = '%1.3e'
        elif d < 1e-1:
            fmt = '%1.3f'
        elif d > 1e5:
            fmt = '%1.1e'
        elif d > 10:
            fmt = '%1.1f'
        elif d > 1:
            fmt = '%1.2f'
        else:
            fmt = '%1.3f'
        s = fmt % x
        tup = s.split('e')
        if len(tup) == 2:
            mantissa = tup[0].rstrip('0').rstrip('.')
            sign = tup[1][0].replace('+', '')
            exponent = tup[1][1:].lstrip('0')
            s = '%se%s%s' % (mantissa, sign, exponent)
        else:
            s = s.rstrip('0').rstrip('.')
        return s

    def __call__(self, x, pos=None):
        xmin, xmax = self.axis.get_view_interval()
        xmin, xmax = self.rescale(xmin), self.rescale(xmax)
        d = abs(xmax - xmin)
        x = self.rescale(x)
        s = self.pprint_val(x, d)
        return s
