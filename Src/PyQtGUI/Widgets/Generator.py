# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Widgets/Generator.py
# @brief     Here we can generate some Widgets
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QWidget, QDockWidget, QScrollArea

class WidgetGenerator:
    """The GUI elements will typically belong to one of the few
    possible categories. The generator will make it easier
    to wrap them in some common elements to make them
    dockable, scrollable, etc.
    """

    def wrapWidget(self,
                   *args,
                   cls: QWidget =None,
                   parent: QWidget =None,
                   name: str = "",
                   scrollable: bool =False,
                   dockable: bool =False,
                   acceptsDrops: bool =True,
                   **kwargs):
        """Takes the constructor for any QWidget
        and creates additional widgets around it
        to enable docking, scrolling, etc.

        Keyword Arguments:
            cls -- the PyQt widget to be created (default: {None})
            parent -- parent QObject for the widget (default: {None})
            name -- name, if needed (default: {""})
            scrollable -- if yes, create a QScrollArea (default: {False})
            dockable -- if yes, create a QDockWidget (default: {False})

        Returns:
            base, instance
            base is the object to be placed in the GUI layout
            instance is the requested widget, which can now
            be configured and connected.
        """
        next_parent = parent
        base = None
        if dockable:
            docker = QDockWidget(name, parent=parent)
            docker.setObjectName(name+"_dockWidget")
            next_parent = docker
            if base is None:
                base = docker
        if scrollable:
            scroller = QScrollArea(next_parent)
            next_parent = scroller
            if base is None:
                base = scroller
        instance = cls(*args, parent=next_parent, **kwargs)
        if acceptsDrops:
            instance.setAcceptDrops(True)
        centre = instance
        if base is None:
            base = instance
        if scrollable:
            scroller.setWidget(centre)
            centre = scroller
        if dockable:
            docker.setWidget(centre)
        return base, instance

        

