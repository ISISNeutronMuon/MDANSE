#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from qtpy.QtWidgets import QWidget, QDockWidget, QScrollArea


class WidgetGenerator:
    """The GUI elements will typically belong to one of the few
    possible categories. The generator will make it easier
    to wrap them in some common elements to make them
    dockable, scrollable, etc.
    """

    def wrapWidget(
        self,
        *args,
        cls: QWidget = None,
        parent: QWidget = None,
        name: str = "",
        scrollable: bool = False,
        dockable: bool = False,
        acceptsDrops: bool = True,
        **kwargs,
    ):
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
            docker.setObjectName(name + "_dockWidget")
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
