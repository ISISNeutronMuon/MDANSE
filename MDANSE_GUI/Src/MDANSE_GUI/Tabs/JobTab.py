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

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Widgets.ActionDialog import ActionDialog
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Views.ActionsTree import ActionsTree


class JobTab(GeneralTab):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model.populateTree()
        self._core.add_button("Show the job dialog!", self.show_action_dialog)

    @Slot()
    def show_action_dialog(self):
        dialog = ActionDialog
        current_item = self._core.current_item()
        if current_item is None:
            return
        converter = IJob.create(current_item.text())
        try:
            dialog_instance = dialog(
                self._core, converter=converter, source_object=self.current_object
            )
        except Exception as e:
            self.error(repr(e))
        dialog_instance.new_thread_objects.connect(self.backend.job_holder.startThread)
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
            model=JobTree(),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Analysis",
                footer="Look up our Read The Docs page:"
                + "https://mdanse.readthedocs.io/en/protos/",
            ),
            layout=DoublePanel,
            label_text="""This is the list of jobs you can run using MDANSE.
Pick a job to see additional information.
Use the button to start a job.
""",
        )
        return the_tab

    @classmethod
    def gui_instance(
        cls, parent: QWidget, name: str, session: LocalSession, settings, logger
    ):
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=JobTree(),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Analysis",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
            layout=DoublePanel,
            label_text="""This is the list of jobs you can run using MDANSE.
Pick a job to see additional information.
Use the button to start a job.
""",
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = JobTab(
        window,
        name="AvailableJobs",
        model=JobTree(),
        view=ActionsTree(),
        visualiser=TextInfo(),
        layout=DoublePanel,
        label_text="""This is the list of jobs you can run using MDANSE.
Pick a job to see additional information.
Use the button to start a job.
""",
    )
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
