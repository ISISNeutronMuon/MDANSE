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

from PyQt6.QtWidgets import QWidget, QDockWidget, QScrollArea

class WidgetGenerator:
    """The GUI elements will typically belong to one of the few
    possible categories. The generator will make it easier
    to wrap them in some common elements to make them
    dockable, scrollable, etc.
    """

    def wrapWidget(self, cls: QWidget =None,
                   parent: QWidget =None,
                   name: str = "",
                   scrollable: bool =False,
                   dockable: bool =False,
                   **kwargs):
        """Takes the constructor for any QWidget
        and creates additional widgets around it
        to enable docking, scrolling, etc.

        Keyword Arguments:
            cls -- _description_ (default: {None})
            parent -- _description_ (default: {None})
            name -- _description_ (default: {""})
            scrollable -- _description_ (default: {False})
            dockable -- _description_ (default: {False})

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
            next_parent = docker
            if base is None:
                base = docker
        if scrollable:
            scroller = QScrollArea(next_parent)
            next_parent = scroller
            if base is None:
                base = scroller
        instance = cls(next_parent, **kwargs)
        if base is None:
            base = instance
        return base, instance

        

