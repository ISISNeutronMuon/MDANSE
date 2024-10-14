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


from typing import Dict, Tuple

from qtpy.QtCore import QObject, Slot, QMessageLogger
from qtpy.QtWidgets import QListView

from MDANSE.MLogging import LOG
from MDANSE.Framework.Units import measure, unit_lookup

from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo


class GeneralTab(QObject):
    """This object connects different elements of a GUI tab,
    such as the data model, view, visualised, layout,
    session, settings and project, all of them relevant
    to the MDANSE_GUI design.

    The idea of tying the well-defined GUI elements into
    a fairly abstract concept of a 'general tab' is intended
    to give the programmers enough flexibility to change the
    behaviour of GUI sections while keeping the common API
    for accessing them from the outside.
    """

    def __init__(self, *args, **kwargs):
        self._name = kwargs.pop("name", "Unnamed GUI part")
        self._session = kwargs.pop("session", LocalSession())
        _ = kwargs.pop("settings", None)
        self._settings = self._session.obtain_settings(self)
        try:
            self._global_settings = self._session.main_settings()
        except AttributeError:
            self._global_settings = None
        self._model = kwargs.pop("model", None)
        self._visualiser = kwargs.pop("visualiser", TextInfo())
        self._view = kwargs.pop("view", QListView())
        self._logger = kwargs.pop("logger", QMessageLogger())
        layout = kwargs.pop("layout", DoublePanel)
        label_text = kwargs.pop("label_text", "An abstract GUI element")
        super().__init__(*args, **kwargs)
        self._core = layout(
            **{
                "data_side": self._view,
                "visualiser_side": self._visualiser,
                "tab_reference": self,
            }
        )
        if self._model is not None:
            self._core.set_model(self._model)
        self._core.set_label_text(label_text)
        self.propagate_session()

    def grouped_settings(self):
        """This method tells the Session object what settings
        this Tab will store in its settings file,
        and what each of the settings means.

        This way each GUI component can have its own settings
        without interfering with the others, and the user
        does not risk breaking all the settings by
        mangling a single file.

        Returns
        -------
        List[str, Dict[str, str], Dict[str, str]]
        """
        group1 = [
            "Generic settings",  # name of the group of settings
            {"path": "."},  # a dictionary of settings
            {
                "path": "The path last used by this GUI element."
            },  # a dictionary of comments
        ]
        group2 = [
            "units",  # name of the group of settings
            {"energy": "meV", "time": "fs", "distance": "ang", "reciprocal": "1/ang"},
            {
                "energy": "The unit of energy preferred by the user.",
                "time": "The unit of time preferred by the user.",
                "distance": "The unit of distance preferred by the user",
                "reciprocal": "The momentum (transfer) unit preferred by the user",
            },
        ]
        return [group1, group2]

    def connect_units(self):
        if self._visualiser is not None:
            if self._visualiser._unit_lookup is None:
                LOG.debug(f"Visualiser {self._visualiser} has no unit lookup")
                self._visualiser._unit_lookup = self

    def conversion_factor(self, input_unit: str) -> Tuple[float, str]:
        """Finds the conversion factor from an input unit
        to the unit preferred by the user for a given
        physical property.

        Parameters
        ----------
        input_unit : str
            Name/abbreviation of a physical unit

        Returns
        -------
        Tuple[float, str]
            factor F and text label str
            Conversion factor F for converting from the input unit
            to the unit saved by the LocalSession instance.
            The conversion will be done outside of this
            function, following the formula:
            converted_value = F * input_value
        """
        conversion_factor = 1.0
        target_unit = input_unit
        property = unit_lookup.get(input_unit, "unknown")
        unit_group = self._settings.group("units").as_dict()
        backup_group = self._global_settings.group("units").as_dict()
        if property not in unit_group:
            if property not in backup_group:
                return conversion_factor, target_unit
            else:
                target_unit = backup_group[property]
        else:
            target_unit = unit_group[property]
        try:
            conversion_factor = measure(1.0, input_unit, equivalent=True).toval(
                target_unit
            )
        except:
            target_unit = self._settings.default_value("units", property)
            conversion_factor = measure(1.0, input_unit, equivalent=True).toval(
                target_unit
            )
        return conversion_factor, target_unit

    def get_path(self, path_key: str):
        paths_group = self._settings.group("paths")
        try:
            path = paths_group.get(path_key)
        except KeyError:
            paths_group.add(
                path_key, ".", f"Filesystem path recently used by {path_key}"
            )
            path = "."
        return path

    def set_path(self, path_key: str, path_value: str):
        paths_group = self._settings.group("paths")
        if not paths_group.set(path_key, path_value):
            paths_group.add(
                path_key, path_value, f"Filesystem path recently used by {path_key}"
            )

    @Slot()
    def save_state(self):
        self._session.save_state(self)

    def load_state(self):
        self._session.load_state(self)

    def propagate_session(self):
        for target in [self._model, self._visualiser, self._view, self._logger]:
            if target is not None:
                target._session = self._session

    @Slot(str)
    def critical(self, message: str):
        LOG.critical(message)

    @Slot(str)
    def warning(self, message: str):
        LOG.warning(message)

    @Slot(str)
    def error(self, message: str):
        LOG.error(message)

    @Slot(str)
    def debug(self, message: str):
        LOG.debug(message)

    @Slot(str)
    def info(self, message: str):
        LOG.info(message)

    @Slot(str)
    def fatal(self, message: str):
        LOG.critical(message)
