from MDANSE import REGISTRY
from MDANSE.GUI.Widgets.SingleChoiceWidget import SingleChoiceWidget

class GroupingLevelWidget(SingleChoiceWidget):
    
    label = "Group coordinates by"

REGISTRY["grouping_level"] = GroupingLevelWidget
