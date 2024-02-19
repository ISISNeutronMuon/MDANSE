from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Slot, Signal

from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewer
from MDANSE_GUI.MolecularViewer.Controls import ViewerControls


class View3D(QWidget):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        controls = ViewerControls(self)
        viewer = MolecularViewer(controls)
        controls.setViewer(viewer)
        layout.addWidget(controls)
        self._viewer = viewer
        self._controls = controls

    @Slot(object)
    def update_panel(self, fullpath: object):
        print(fullpath)
        if fullpath == "":
            # a trajectory was deleted and the view emitted an empty
            # string we need to clear the panel
            self._viewer.clear_panel()
            return

        try:
            self._viewer._new_trajectory(fullpath)
        except AttributeError:
            self.error.emit(f"3D View could not visualise {fullpath}")
            self._viewer.clear_trajectory()
