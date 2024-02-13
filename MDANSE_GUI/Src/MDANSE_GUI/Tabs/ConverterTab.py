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


from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QWidget

from MDANSE.Framework.Converters.Converter import Converter

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Widgets.ActionDialog import ActionDialog
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Views.ActionsTree import ActionsTree


tab_label = """Convert your trajectory to the MDANSE MDT format.
If you cannot find the converter for your MD engine, the
ASE converter can be tried as a backup option.
"""


class ConverterTab(GeneralTab):
    """The tab for choosing and starting a new job."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_trajectory = ""
        self._job_starter = None
        self._core.add_button("Show the job dialog!", self.show_action_dialog)

    def set_job_starter(self, job_starter):
        self._job_starter = job_starter

    @Slot(str)
    def set_current_trajectory(self, new_name: str):
        self._current_trajectory = new_name

    @Slot()
    def show_action_dialog(self):
        dialog = ActionDialog
        current_item = self._core.current_item()
        if current_item is None:
            return
        try:
            converter = Converter.create(current_item.text())
        except ValueError as e:
            print(f"Failed: {e}")
            return
        except IndexError as e:
            print(f"Failed: {e}")
            return
        try:
            dialog_instance = dialog(
                self._core,
                job_name=current_item.text(),
                trajectory=self._current_trajectory,
            )
        except Exception as e:
            self.error(repr(e))
        if self._job_starter is not None:
            dialog_instance.new_thread_objects.connect(self._job_starter.startThread)
        dialog_instance.show()
        try:
            result = dialog_instance.exec()
        except Exception as e:
            self.error(repr(e))

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="AvailableJobs",
            model=JobTree(parent_class=Converter),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Converter",
                footer="Look up our Read The Docs page:"
                + "https://mdanse.readthedocs.io/en/protos/",
            ),
            layout=DoublePanel,
            label_text=tab_label,
        )
        return the_tab

    @classmethod
    def gui_instance(
        cls,
        parent: QWidget,
        name: str,
        session: LocalSession,
        settings,
        logger,
        **kwargs,
    ):
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", JobTree(parent_class=Converter)),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Converter",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
            layout=DoublePanel,
            label_text=tab_label,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = ConverterTab(
        window,
        name="AvailableJobs",
        model=JobTree(parent_class=Converter),
        view=ActionsTree(),
        visualiser=TextInfo(
            header="MDANSE Converters",
            footer="Look up our "
            + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
            + " page.",
        ),
        layout=DoublePanel,
        label_text=tab_label,
    )
    the_tab._current_trajectory = "/Users/maciej.bartkowiak/an_example/BLAH.mdt"
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
