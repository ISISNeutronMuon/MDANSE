#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext

import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)

from qtpy.QtWidgets import (
    QWidget,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QVBoxLayout,
)
from qtpy.QtCore import Slot, Signal, QObject, Qt

from MDANSE.Framework.Units import measure
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter


class PlotSettings(QWidget):

    plot_settings_changed = Signal()

    def __init__(self, *args, settings=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._settings = settings
        self._unit_fields = {}
        self.make_layout()

    @Slot(str)
    def set_style(self, style_name: str):
        try:
            mpl.style.use(style_name)
        except:
            print(f"Could not set matplotlib style to {style_name}")
        else:
            self.plot_settings_changed.emit()

    @Slot(str)
    def set_cmap(self, cmap_name: str):
        colour_group = self._settings.group("colours")
        if not colour_group.set("colormap", cmap_name):
            colour_group.add(
                "colormap",
                cmap_name,
                "Name of the matplotlib colormap to be used in 2D plots.",
            )
        self.plot_settings_changed.emit()

    @Slot(object)
    def update_plot_details(self, input):
        """Dummy method, for compatibility only"""

    @Slot()
    def update_units(self):
        unit_group = self._settings.group("units")
        try:
            energy = self._unit_fields["energy"].currentText()
        except:
            pass
        else:
            try:
                measure(1.0, "rad/ps", equivalent=True).toval(energy)
            except:
                pass
            else:
                if not unit_group.set("energy", energy):
                    unit_group.add(
                        "energy",
                        energy,
                        "Preferred physical unit for expressing energy.",
                    )
        try:
            time = self._unit_fields["time"].currentText()
        except:
            pass
        else:
            try:
                measure(1.0, "ps").toval(time)
            except:
                pass
            else:
                if not unit_group.set("time", time):
                    unit_group.add(
                        "time", time, "Preferred physical unit for expressing time."
                    )
        try:
            distance = self._unit_fields["distance"].currentText()
        except:
            pass
        else:
            try:
                measure(1.0, "nm").toval(distance)
            except:
                pass
            else:
                if not unit_group.set("distance", distance):
                    unit_group.add(
                        "distance",
                        distance,
                        "Preferred physical unit for expressing distance.",
                    )
        try:
            reciprocal = self._unit_fields["reciprocal"].currentText()
        except:
            pass
        else:
            try:
                measure(1.0, "1/nm").toval(reciprocal)
            except:
                pass
            else:
                if not unit_group.set("reciprocal", reciprocal):
                    unit_group.add(
                        "reciprocal",
                        reciprocal,
                        "Preferred physical unit for expressing (quasi)momentum, i.e. reciprocal space units.",
                    )
        self.plot_settings_changed.emit()

    def make_layout(self, width=12.0, height=9.0, dpi=100):
        """Creates a matplotlib figure for plotting

        Parameters
        ----------
        width : float, optional
            Figure width in inches, by default 12.0
        height : float, optional
            Figure height in inches, by default 9.0
        dpi : int, optional
            Figure resolution in dots per inch, by default 100

        Returns
        -------
        QWidget
            a widget containing both the figure and a toolbar below
        """
        layout = QVBoxLayout(self)
        top_layout = QFormLayout()
        style_selector = QComboBox(self)
        style_selector.addItem("default")
        style_selector.addItems(mpl.style.available)
        style_selector.setCurrentText("default")
        style_selector.currentTextChanged.connect(self.set_style)
        top_layout.addRow("Matplotlib style:", style_selector)
        colour_group = self._settings.group("colours")
        try:
            current_cmap = colour_group.get("colormap")
        except KeyError:
            colour_group.add(
                "colormap",
                "viridis",
                "Name of the matplotlib colormap to be used in 2D plots.",
            )
            current_cmap = "viridis"
        cmap_selector = QComboBox(self)
        cmap_selector.addItems(mpl.colormaps())
        cmap_selector.setCurrentText(current_cmap)
        cmap_selector.currentTextChanged.connect(self.set_cmap)
        top_layout.addRow("Colormap:", cmap_selector)
        layout.addLayout(top_layout)
        box = QGroupBox("Units", self)
        layout.addWidget(box)
        unit_layout = QFormLayout(box)
        box.setLayout(unit_layout)
        energy_combo = QComboBox(box)
        energy_combo.addItems(["meV", "1/cm", "THz"])
        energy_combo.currentTextChanged.connect(self.update_units)
        time_combo = QComboBox(box)
        time_combo.addItems(["fs", "ps", "ns"])
        time_combo.currentTextChanged.connect(self.update_units)
        distance_combo = QComboBox(box)
        distance_combo.addItems(["ang", "Bohr", "nm", "pm"])
        distance_combo.currentTextChanged.connect(self.update_units)
        reciprocal_combo = QComboBox(box)
        reciprocal_combo.addItems(["1/ang", "1/Bohr", "1/nm", "1/pm"])
        reciprocal_combo.currentTextChanged.connect(self.update_units)
        unit_layout.addRow("Energy unit:", energy_combo)
        unit_layout.addRow("Time unit:", time_combo)
        unit_layout.addRow("Distance unit:", distance_combo)
        unit_layout.addRow("Reciprocal space unit:", reciprocal_combo)
        self._unit_fields["energy"] = energy_combo
        self._unit_fields["time"] = time_combo
        self._unit_fields["distance"] = distance_combo
        self._unit_fields["reciprocal"] = reciprocal_combo
