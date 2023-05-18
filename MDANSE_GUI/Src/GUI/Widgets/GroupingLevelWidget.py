# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/GroupingLevelWidget.py
# @brief     Implements module/class/test GroupingLevelWidget
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

class GroupingLevelWidget(SingleChoiceWidget):
    
    label = "Group coordinates by"

REGISTRY["grouping_level"] = GroupingLevelWidget
