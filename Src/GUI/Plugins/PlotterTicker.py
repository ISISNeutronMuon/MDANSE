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
