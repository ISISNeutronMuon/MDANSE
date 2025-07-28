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

from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG


class PlotSettings(QWidget):
    plot_settings_changed = Signal()

    def __init__(self, *args, settings=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._settings = settings
        self._unit_fields = {}
        self.plot_settings_changed.connect(self.update_settings_file)

    @Slot()
    def update_settings_file(self):
        self._settings.save_values()

    @Slot(str)
    def set_style(self, style_name: str):
        mpl_group = self._settings.group("matplotlib")
        if not mpl_group.set("style", style_name):
            mpl_group.add(
                "style",
                style_name,
                "Name of the matplotlib style to be used for plotting.",
            )
        try:
            mpl.style.use(style_name)
        except Exception:
            LOG.error(f"Could not set matplotlib style to {style_name}")
            backup_style = self._unit_lookup._settings.default_value(
                "matplotlib", "style"
            )
            if backup_style is None:
                mpl.style.use("default")
            else:
                mpl.style.use(backup_style)
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

    @Slot()
    def update_units(self):
        unit_group = self._settings.group("units")
        try:
            energy = self._unit_fields["energy"].currentText()
        except Exception:
            LOG.warning("Could not get the energy unit from GUI")
        else:
            try:
                measure(1.0, "rad/ps", equivalent=True).toval(energy)
            except Exception:
                energy = self._settings.default_value("units", "energy")
            else:
                if not unit_group.set("energy", energy):
                    unit_group.add(
                        "energy",
                        energy,
                        "Preferred physical unit for expressing energy.",
                    )
        try:
            time = self._unit_fields["time"].currentText()
        except Exception:
            LOG.warning("Could not get the time unit from GUI")
        else:
            try:
                measure(1.0, "ps").toval(time)
            except Exception:
                time = self._settings.default_value("units", "time")
            else:
                if not unit_group.set("time", time):
                    unit_group.add(
                        "time", time, "Preferred physical unit for expressing time."
                    )
        try:
            distance = self._unit_fields["distance"].currentText()
        except Exception:
            LOG.warning("Could not get the distance unit from GUI")
        else:
            try:
                measure(1.0, "nm").toval(distance)
            except Exception:
                distance = self._settings.default_value("units", "distance")
            else:
                if not unit_group.set("distance", distance):
                    unit_group.add(
                        "distance",
                        distance,
                        "Preferred physical unit for expressing distance.",
                    )
        try:
            reciprocal = self._unit_fields["reciprocal"].currentText()
        except Exception:
            LOG.warning("Could not get the reciprocal space unit from GUI")
        else:
            try:
                measure(1.0, "1/nm").toval(reciprocal)
            except Exception:
                reciprocal = self._settings.default_value("units", "reciprocal")
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
        style_list_mpl = mpl.style.available
        style_list_filtered = [x for x in style_list_mpl if x[0] != "_"]
        style_list_filtered = [x for x in style_list_filtered if "lorbli" not in x]
        style_list_filtered = [x for x in style_list_filtered if x not in ["fast"]]
        style_selector.addItems(style_list_filtered)
        try:
            style_string = self._settings.group("matplotlib").get("style")
        except Exception:
            style_string = "default"
        style_selector.setCurrentText(style_string)
        style_selector.currentTextChanged.connect(self.set_style)
        top_layout.addRow("Matplotlib style:", style_selector)
        try:
            colour_group = self._settings.group("colours")
            try:
                current_cmap = colour_group.get("colormap")
            except KeyError:
                LOG.warning("Could not get colormap from colours")
                colour_group.add(
                    "colormap",
                    "viridis",
                    "Name of the matplotlib colormap to be used in 2D plots.",
                )
                current_cmap = "viridis"
            else:
                if current_cmap not in mpl.colormaps():
                    current_cmap = "viridis"
        except Exception:
            LOG.warning("Could not get the colours group")
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
        try:
            unit_group = self._settings.group("units")
        except Exception:
            pass
        else:
            current_energy = unit_group.get("energy")
            current_time = unit_group.get("time")
            current_distance = unit_group.get("distance")
            current_reciprocal = unit_group.get("reciprocal")
            energy_combo.setCurrentText(current_energy)
            time_combo.setCurrentText(current_time)
            distance_combo.setCurrentText(current_distance)
            reciprocal_combo.setCurrentText(current_reciprocal)
