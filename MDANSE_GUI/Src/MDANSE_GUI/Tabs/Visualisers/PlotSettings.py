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
from __future__ import annotations

import matplotlib.pyplot as mpl
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Core.Settings import Option, Settings
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE_GUI.Session.Settings import GUISettings


@Settings.parametrise(
    colourmap=Option(
        "viridis",
        group="matplotlib",
        comment="Name of the matplotlib colormap to be used in 2D plots.",
    ),
    mpl_style=Option(
        "default",
        group="matplotlib",
        comment="Name of the matplotlib style to be used for plotting.",
    ),
)
class PlotSettings(QWidget):
    plot_settings_changed = Signal()

    def __init__(self, *args, settings: GUISettings | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._settings = settings or GUISettings(save=False)
        self._unit_fields = {}
        self.plot_settings_changed.connect(Settings.save)

    @Slot(str)
    def set_style(self, style_name: str):
        try:
            mpl.style.use(style_name)
            self.mpl_style = style_name
        except Exception:
            LOG.error(f"Could not set matplotlib style to {style_name}")
            backup_style = Settings.get_default("matplotlib", "mpl_style")
            if backup_style is None:
                mpl.style.use("default")
                self.mpl_style = "default"
            else:
                mpl.style.use(backup_style)
                self.mpl_style = backup_style
        else:
            self.plot_settings_changed.emit()

    @Slot(str)
    def set_cmap(self, cmap_name: str):
        self.colourmap = cmap_name
        self.plot_settings_changed.emit()

    @Slot()
    def update_units(self):
        for dim, trial in {
            "energy": "rad/ps",
            "time": "ps",
            "distance": "nm",
            "reciprocal": "1/nm",
        }.items():
            try:
                read = self._unit_fields[dim].currentText()
            except Exception:
                LOG.warning("Could not get the %s unit from GUI", dim)
                continue

            try:
                measure(1.0, trial, equivalent=True).toval(read)
            except Exception:
                read = Settings.get_default("units", dim)

            self._settings["units", dim] = read

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

        style_list_mpl = mpl.style.available
        style_list_filtered = [x for x in style_list_mpl if x[0] != "_"]
        style_list_filtered = [x for x in style_list_filtered if "lorbli" not in x]
        style_list_filtered = [x for x in style_list_filtered if x != "fast"]

        style_selector.addItems(style_list_filtered)
        style_string: str = self.mpl_style
        style_selector.setCurrentText(style_string)
        style_selector.currentTextChanged.connect(self.set_style)
        top_layout.addRow("Matplotlib style:", style_selector)

        if (current_cmap := self.colourmap) not in mpl.colormaps():
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

        current_energy = self._settings["units", "energy"]
        current_time = self._settings["units", "time"]
        current_distance = self._settings["units", "distance"]
        current_reciprocal = self._settings["units", "reciprocal"]
        energy_combo.setCurrentText(current_energy)
        time_combo.setCurrentText(current_time)
        distance_combo.setCurrentText(current_distance)
        reciprocal_combo.setCurrentText(current_reciprocal)
