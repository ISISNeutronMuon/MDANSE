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

import os
from abc import abstractmethod
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from qtpy.QtCore import QMessageLogger, QObject, QSettings, Signal, Slot
from qtpy.QtWidgets import QListView, QWidget

from MDANSE.Core.Settings import Option, Settings
from MDANSE.Framework.Units import measure, unit_lookup
from MDANSE.MLogging import LOG
from MDANSE_GUI.Session.Session import Session
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo

if TYPE_CHECKING:
    from qtpy.QtWidgets import QAbstractItemView

    from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
    from MDANSE_GUI.Tabs.Layouts.SinglePanel import SinglePanel


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

    notify_user = Signal(int)

    def __init__(
        self,
        *args,
        name: str = "Unnamed GUI part",
        session: Session | None = None,
        qt_settings: QSettings | None = None,
        model: GeneralModel | None = None,
        visualiser: QWidget | None = None,
        view: QAbstractItemView | None = None,
        logger: QMessageLogger | None = None,
        layout: type[SinglePanel | DoublePanel | MultiPanel] = DoublePanel,
        label_text: str = "An abstract GUI element",
        **kwargs,
    ):
        self._my_tab_id = -1
        self._name = name
        self._session = session if session is not None else Session()
        self._settings = self._session._settings

        self._model = model
        self._visualiser = visualiser if visualiser is not None else TextInfo()
        self._view = view if view is not None else QListView()
        self._logger = logger if logger is not None else QMessageLogger()

        super().__init__(*args, **kwargs)

        self._core = layout(
            data_side=self._view,
            visualiser_side=self._visualiser,
            tab_reference=self,
        )
        if self._model is not None:
            self._core.set_model(self._model)
        self._core.set_label_text(label_text)
        self.propagate_session()

    def set_my_id(self, tab_id: int):
        self._my_tab_id = tab_id

    @Slot()
    def tab_notification(self):
        self.notify_user.emit(self._my_tab_id)

    def connect_units(self):
        if self._visualiser is not None and self._visualiser._unit_lookup is None:
            LOG.debug(f"Visualiser {self._visualiser} has no unit lookup")
            self._visualiser._unit_lookup = self

    def conversion_factor(self, input_unit: str) -> tuple[float, str]:
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
            to the unit saved by the Session instance.
            The conversion will be done outside of this
            function, following the formula:
            converted_value = F * input_value
        """
        property = unit_lookup.get(input_unit, "unknown")
        target_unit = Settings.get_opt("units", property)

        try:
            conversion_factor = measure(1.0, input_unit, equivalent=True).toval(
                target_unit
            )
        except Exception:
            target_unit = Settings.get_default("units", property)
            conversion_factor = measure(1.0, input_unit, equivalent=True).toval(
                target_unit
            )
        return conversion_factor, target_unit

    def get_path(self, path_key: str):
        return Settings.get_opt_w_default(
            f"{type(self).__name__}.paths",
            path_key,
            str(Path.cwd()),
            f"Last path used by {path_key}",
        )

    def set_path(self, path_key: str, path_value: str):
        self._settings[f"{type(self).__name__}.paths", path_key] = path_value
        Settings.save()

    @Slot()
    def save_state(self):
        self._session.save()

    # def load_state(self):
    #     self._session.load(self)

    def propagate_session(self):
        for target in [self._model, self._visualiser, self._view, self._logger]:
            if target is not None:
                target._session = self._session

    @classmethod
    @abstractmethod
    def gui_instance(
        cls,
        parent: QWidget,
        *,
        name: str,
        session: Session,
        qt_settings: QSettings | None,
        logger: QMessageLogger,
        **kwargs,
    ): ...
