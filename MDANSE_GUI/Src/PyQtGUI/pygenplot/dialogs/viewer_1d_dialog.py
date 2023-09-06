from qtpy import QtWidgets


class Viewer1DDialog(QtWidgets.QDalog):
    def __init__(self, plot_1d_model, *args, **kwargs):
        super(Viewer1DDialog, self).__init__(*args, **kwargs)

        self._plot_1d_model = plot_1d_model

        self._build()

    def _build(self):
        main_layout = QtWidgets.QVBoxLayout()

        self._data_table_view = QtWidgets.QTableView()

        self.setLayout(main_layout)
