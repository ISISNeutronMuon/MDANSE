from qtpy.QtCore import QObject, Slot, Signal


# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/RegistryViewer.py
# @brief     Shows the MDANSE jobs. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from qtpy.QtCore import QObject, Slot, Signal, QMessageLogger
from qtpy.QtWidgets import QListView

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.PyQtGUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.PyQtGUI.Session.LocalSession import LocalSession
from MDANSE_GUI.PyQtGUI.Tabs.Settings.LocalSettings import LocalSettings
from MDANSE_GUI.PyQtGUI.Tabs.Visualisers.TextInfo import TextInfo


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
        self._settings = kwargs.pop("settings", LocalSettings())
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
        self._core.set_model(self._model)
        self._core.set_label_text(label_text)
        self._core.connect_logging

    @Slot()
    def save_state(self):
        self._session.save_state(self)

    def load_state(self):
        self._session.load_state(self)

    @Slot(str)
    def critical(self, message: str):
        self._logger.critical(message)

    @Slot(str)
    def warning(self, message: str):
        self._logger.warning(message)

    @Slot(str)
    def error(self, message: str):
        self._logger.critical(message)

    @Slot(str)
    def debug(self, message: str):
        self._logger.debug(message)

    @Slot(str)
    def info(self, message: str):
        self._logger.info(message)

    @Slot(str)
    def fatal(self, message: str):
        self._logger.fatal(message)
