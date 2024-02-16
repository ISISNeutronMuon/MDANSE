from MDANSE.Framework.Jobs.IJob import IJob

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Signal, QSortFilterProxyModel, QModelIndex
from qtpy.QtCore import Qt


class JobTree(QStandardItemModel):
    """RegistryTree creates a tree structure
    of QStandardItem objects, and stores information
    about the names and docstrings of different
    classes contained in the IJob object.

    It inherits the QStandardItemModel, so it can be
    used in the Qt data/view/proxy model.
    """

    doc_string = Signal(str)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        parent_class = kwargs.pop("parent_class", IJob)
        filter = kwargs.pop("filter", None)
        super().__init__(*args, **kwargs)

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
        for class_name, class_object in full_dict.items():
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
        if hasattr(thing, "category"):
            if filter:
                if filter in thing.category:
                    parent = self.parentsFromCategories(thing.category)
                else:
                    return
            else:
                parent = self.parentsFromCategories(thing.category)
        else:
            parent = self.invisibleRootItem()
        parent.appendRow(new_node)

    def parentsFromCategories(self, category_tuple):
        """Returns the parent node for a node that belongs to the
        category specified by categore_tuple. Also makes sure that
        the parent nodes exist (or creates them if they don't).

        Arguments:
            category_tuple -- category names (str) in the sequence in which
                they should be placed in the tree structure.

        Returns:
            QStandardItem - the node of the last item in 'category_tuple'
        """
        parent = self.invisibleRootItem()
        for cat_string in category_tuple:
            if not cat_string in self._categories.keys():
                current_node = QStandardItem(cat_string)
                parent.appendRow(current_node)
                parent = current_node
                self._categories[cat_string] = current_node
            else:
                current_node = self._categories[cat_string]
                parent = current_node
        return current_node
