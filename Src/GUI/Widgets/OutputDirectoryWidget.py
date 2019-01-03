# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/OutputDirectoryWidget.py
# @brief     Implements module/class/test OutputDirectoryWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY

from MDANSE.GUI.Widgets.InputDirectoryWidget import InputDirectoryWidget

class OutputDirectoryWidget(InputDirectoryWidget):
    
    pass
    
REGISTRY["output_directory"] = OutputDirectoryWidget
