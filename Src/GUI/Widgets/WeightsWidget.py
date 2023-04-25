# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/WeightsWidget.py
# @brief     Implements module/class/test WeightsWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY

from MDANSE.GUI.Widgets.SingleChoiceWidget import SingleChoiceWidget

class WeightsWidget(SingleChoiceWidget):
    
    pass

REGISTRY["weights"] = WeightsWidget

