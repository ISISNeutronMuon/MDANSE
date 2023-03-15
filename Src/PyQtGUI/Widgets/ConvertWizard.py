
from typing import Union, Iterable
from collections import OrderedDict
import copy

from icecream import ic
from qtpy.QtWidgets import QDialog, QPushButton, QFileDialog, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QComboBox, QMenu, QLineEdit, QTableView,\
                           QFormLayout, QHBoxLayout, QCheckBox, \
                           QWizard, QWizardPage
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel,\
                        QObject
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel,\
                    QIntValidator, QDoubleValidator, QValidator

from MDANSE.Framework.Jobs.IJob import IJob

# I think that a Trajectory Converter should, in general,
# create a Wizard and not a single Dialog.
# This way LAMMPS could give the user a chance to verify which
# elements were in the system, instead of just failing.
# The idea is similar to Origin and the way Origin creates
# a lengthy wizard interface just to load data from a file.
# The wizard should have a number of stages, which can be
# used or left empty.

# I need to have several stages of processing
# 1. The initial Dialog is created based on settings from the Converter
# 2. The user specifies the input files
# 3. The converter tries to get as much information as possible from the files
# 4. The information gathered is shown to the user, 
# with a possibility of correcting the entries.
# 5. The corrected parameters are passed to the converter, and the job is started.


class ConvertWizard(QWizard):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


