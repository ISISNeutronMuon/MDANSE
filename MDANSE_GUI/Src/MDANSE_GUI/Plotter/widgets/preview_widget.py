# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Plotter/__init__.py
# @brief     root file of Plotter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class PreviewWidget(FigureCanvasQTAgg):
    def __init__(self, *args, **kwargs):
        """Constructor."""
        fig = Figure(figsize=(2, 2))
        self._axes = fig.add_axes([0.0, 0.0, 1.0, 1.0])
        super(PreviewWidget, self).__init__(fig, *args, **kwargs)

    def update_plot(self, data_info):
        """Update the previes plot.

        Args:
            data_info (dict): the information about the data to preview
        """
        self._axes.clear()

        if not data_info["plottable"]:
            self._axes.text(0.2, 0.5, "Data not plottable")
        else:
            ndim = data_info["dimension"]
            if ndim == 1:
                self._axes.plot(data_info["data"])
                self._axes.legend([data_info["variable"]])

            elif ndim == 2:
                self._axes.imshow(
                    data_info["data"], interpolation="nearest", origin="lower"
                )

            else:
                self._axes.text(0.2, 0.5, "No preview available")

        self._axes.set_aspect("auto")
        self.draw()
