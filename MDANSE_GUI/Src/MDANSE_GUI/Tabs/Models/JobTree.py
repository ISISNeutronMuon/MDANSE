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
#
from __future__ import annotations

from collections import defaultdict

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import IJob


class JobTree(QStandardItemModel):
    """Creates a tree structure
    of QStandardItem objects, and stores information
    about the names and docstrings of different
    classes contained in the IJob object.

    It inherits the QStandardItemModel, so it can be
    used in the Qt data/view/proxy model.
    """

    doc_string = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        *args,
        parent_class: IJob | Converter = IJob,
        hidden_levels: int = 0,
        **kwargs,
    ):
        filter = kwargs.pop("filter", None)
        super().__init__(*args, **kwargs)

        self._hidden_levels = hidden_levels
        self._nodes = {}  # dict of {number: QStandardItem}
        self._docstrings = {}  # dict of {number: str}
        self._values = {}  # dict of {number: str}

        self._categories = {}
        self._jobs = {}

        self._by_ancestor = {}  # dict of list[int]

        self.nodecounter = 0  # each node is given a unique number

        self.populateTree(parent_class=parent_class, filter=filter)

    def populateTree(self, parent_class=None, filter=None):
        """This function starts the recursive process of scanning
        the registry tree. Only called once on startup.
        """
        if parent_class is None:
            parent_class = IJob
        full_dict = parent_class.indirect_subclass_dictionary()
        sorted_keys = sorted(full_dict)
        cat_dicts = defaultdict(list)
        for class_name in sorted_keys:
            if not full_dict[class_name].enabled:
                continue
            cat_tuple = getattr(full_dict[class_name], "category", None)
            if cat_tuple and len(cat_tuple) > 1:
                cat_dicts[cat_tuple[0]].append(cat_tuple[1])

        cat_dicts = {cat: sorted(cat_dicts[cat]) for cat in sorted(cat_dicts)}
        for cat, vals in cat_dicts.items():
            if filter and cat not in filter:
                for subcat in vals:
                    self.parentsFromCategories((cat, subcat))
        for class_name in sorted_keys:
            class_object = full_dict[class_name]
            if class_object.enabled:
                self.createNode(class_name, class_object, filter)

    def createNode(self, name: str, thing, filter: str = ""):
        """Creates a new QStandardItem. It will store
        the node number as user data. The 'thing' passed to this method
        will be stored by the model in an internal dictionary, where
        the node number is the key

        Arguments:
            name -- the name of the new node
            thing -- any Python object to be stored and attached to the node
            filter -- a string which must appear in the category tuple
        """
        new_node = QStandardItem(name)
        new_number = self.nodecounter + 1
        self.nodecounter += 1
        new_node.setData(new_number, role=Qt.ItemDataRole.UserRole)
        self._nodes[new_number] = new_node
        self._values[new_number] = thing
        self._docstrings[new_number] = thing.__doc__
        try:
            self._docstrings[new_number] += "\n" + thing.build_doc(use_html_table=True)
        except AttributeError:
            pass
        except TypeError:
            pass
        if hasattr(thing, "category"):
            trimmed_category = thing.category[self._hidden_levels :]
            if filter:
                if filter not in thing.category:
                    parent = self.parentsFromCategories(trimmed_category)
                else:
                    return
            else:
                parent = self.parentsFromCategories(trimmed_category)
        else:
            parent = self.invisibleRootItem()
        parent.appendRow(new_node)

    def parentsFromCategories(self, category_tuple):
        """Returns the parent node for a node that belongs to the
        category specified by category_tuple. Also makes sure that
        the parent nodes exist (or creates them if they don't).

        Arguments:
            category_tuple -- category names (str) in the sequence in which
                they should be placed in the tree structure.

        Returns:
            QStandardItem - the node of the last item in 'category_tuple'
        """
        parent = self.invisibleRootItem()
        for cat_string in category_tuple:
            if cat_string not in self._categories:
                current_node = QStandardItem(cat_string)
                parent.appendRow(current_node)
                parent = current_node
                self._categories[cat_string] = current_node
            else:
                current_node = self._categories[cat_string]
                parent = current_node
        return current_node
