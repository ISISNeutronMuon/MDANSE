import logging
import sys

from qtpy import QtCore, QtWidgets

from MDANSE_GUI.PyQtGUI.pygenplot.models.data_tree_model import (
    DATA_ITEMS,
    DataTreeModelError,
)
from MDANSE_GUI.PyQtGUI.pygenplot.models.plot_1d_model import Plot1DModelError
from MDANSE_GUI.PyQtGUI.pygenplot.widgets.data_widget import DataWidget
from MDANSE_GUI.PyQtGUI.pygenplot.widgets.actions_widget import ActionsWidget
from MDANSE_GUI.PyQtGUI.pygenplot.widgets.plot_1d_widget import Plot1DWidget
from MDANSE_GUI.PyQtGUI.pygenplot.widgets.plot_nd_widget import PlotNDWidget
from MDANSE_GUI.PyQtGUI.pygenplot.widgets.preview_widget import PreviewWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent, filename=None):
        """Constructor."""
        super(MainWindow, self).__init__(parent)

        self._build()

        self._build_menu()

        if filename is not None:
            self.add_data(filename)

    def _build(self):
        """Build the main window."""
        self._plots_tab_widget = QtWidgets.QTabWidget(self)
        self._plots_tab_widget.setTabsClosable(True)
        self.setCentralWidget(self._plots_tab_widget)

        self._data_dock_widget = QtWidgets.QDockWidget("Data", self)
        self._data_dock_widget.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self._data_dock_widget.setFloating(False)
        self._data_dock_widget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self._data_widget = DataWidget(self)
        self._data_dock_widget.setWidget(self._data_widget)

        self._actions_dock_widget = QtWidgets.QDockWidget("Actions", self)
        self._actions_dock_widget.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self._actions_dock_widget.setFloating(False)
        self._actions_dock_widget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self._actions_widget = ActionsWidget()
        self._actions_dock_widget.setWidget(self._actions_widget)

        self._preview_dock_widget = QtWidgets.QDockWidget("Preview", self)
        self._preview_dock_widget.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self._preview_dock_widget.setFloating(False)
        self._preview_dock_widget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self._preview_widget = PreviewWidget()
        self._preview_dock_widget.setWidget(self._preview_widget)

        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self._data_dock_widget
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self._actions_dock_widget
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self._preview_dock_widget
        )

        self.resize(1000, 1000)

        self._plots_tab_widget.tabCloseRequested.connect(self.on_close_plot)
        self._actions_widget.plot_in_new_figure.connect(self.on_plot_in_new_figure)
        self._actions_widget.plot_in_current_figure.connect(
            self.on_plot_in_current_figure
        )
        self._actions_widget.units_updated.connect(self.on_units_updated)

        self._data_widget.dataset_selected.connect(self.on_select_dataset)

    def _build_menu(self):
        """Build the menu."""
        menubar = self.menuBar()
        file_menu = QtWidgets.QMenu("&File", self)
        open_file_action = file_menu.addAction("Open")
        open_file_action.triggered.connect(self.on_open_file)
        close_app_action = file_menu.addAction("Exit")
        close_app_action.triggered.connect(self.on_quit_application)
        menubar.addMenu(file_menu)

    def add_data(self, filename):
        """Add data to the data tree  of loaded files.

        Args:
            filename (str): the name of the file
        """
        try:
            data_model = self._data_widget.model()
            data_model.add_data(filename)
        except DataTreeModelError as e:
            print(str(e), ["main", "popup"], "error")
        else:
            print(f"File {filename} successfully opened for reading", ["main"], "info")

    def on_close_plot(self, index):
        """Callback called when a plot tab is closed.

        Args:
            index (int): the index of the plot tab
        """
        widget = self._plots_tab_widget.widget(index)
        widget.close()
        self._plots_tab_widget.removeTab(index)

    def on_open_file(self):
        """Callback called when a file is opened."""
        extensions = " ".join([f"*{k}" for k in DATA_ITEMS.keys()])
        filter_mask = f"Data files {extensions}"
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Data File(s)", "", filter_mask
        )
        if not filename:
            return
        self.add_data(filename)

    def on_plot_in_new_figure(self, plot_type):
        """Callback when the plot in a new figure button is clicked.

        Args:
            plot_type (str): the plot type
        """
        selected_dataset_info = self._data_widget.get_selected_dataset_info()
        if not selected_dataset_info:
            return

        axis_dataset_info = self._data_widget.get_selected_dataset_axis_info()
        if not axis_dataset_info:
            for dinfo in axis_dataset_info:
                if not dinfo["plottable"]:
                    print(
                        f"One or more dependent axis of the dataset is not plottable: {dinfo['status']}",
                        ["main", "popup"],
                        "error",
                    )
                    return

        if not selected_dataset_info["plottable"]:
            print(
                f"The dataset is not plottable: {selected_dataset_info['status']}",
                ["main", "popup"],
                "error",
            )
            return

        if plot_type == "Line":
            try:
                plot_widget = Plot1DWidget(plot_type, axis_dataset_info[0], self)
                plot_widget.add_line(selected_dataset_info)
            except Exception as e:
                print(str(e), ["main", "popup"], "error")
                return
            else:
                self._plots_tab_widget.addTab(
                    plot_widget, selected_dataset_info["variable"]
                )

        elif plot_type == "Image":
            try:
                plot_widget = PlotNDWidget(
                    plot_type, axis_dataset_info, selected_dataset_info, self
                )
            except Exception as e:
                print(str(e), ["main", "popup"], "error")
                return
            else:
                self._plots_tab_widget.addTab(
                    plot_widget, selected_dataset_info["variable"]
                )

        elif plot_type == "2D Slice":
            try:
                plot_widget = PlotNDWidget(
                    plot_type, axis_dataset_info, selected_dataset_info, self
                )
            except Exception as e:
                print(str(e), ["main", "popup"], "error")
                return
            else:
                self._plots_tab_widget.addTab(
                    plot_widget, selected_dataset_info["variable"]
                )

    def on_plot_in_current_figure(self, plot_type):
        """Callback called when the plot in the current figure button is clicked.

        Args:
            plot_type (str): the plot type
        """
        current_widget = self._plots_tab_widget.currentWidget()
        if current_widget is None:
            return

        if current_widget.get_plot_type() != plot_type:
            print("Incompatible plot types", ["main", "popup"], "error")
            return

        if plot_type != "Line":
            return

        selected_dataset_info = self._data_widget.get_selected_dataset_info()

        try:
            current_widget.add_line(selected_dataset_info)
        except Plot1DModelError as e:
            print(str(e), ["main", "popup"], "error")

    def on_quit_application(self):
        """Quit the application."""
        choice = QtWidgets.QMessageBox.question(
            self,
            "Quit",
            "Do you really want to quit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()

    def on_select_dataset(self, dataset_info):
        """Callback when a dataset is selected from the data tree.

        Args:
            dataset_info (dict): the information about the selected dataset
        """
        self._preview_widget.update_plot(dataset_info)
        self._actions_widget.set_data(dataset_info["data"])

    def on_units_updated(self):
        """Callback called when the units dialog has been accepted."""
        self._data_widget.update()
