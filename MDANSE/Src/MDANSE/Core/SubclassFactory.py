#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

import difflib
from typing import TypeVar

Self = TypeVar("Self", bound="SubclassFactory")
# The Self TypeVar is a typing hint indicating that
# a method of a class A will be returning an object
# of type A as well. Since we don't know for which class
# the SubclassFactory metaclass will be used, the return
# type has to be defined this way.
# NOTE: the later versions of Python (3.11) define Self
# as a type explicitly, but for now we have to define it
# ourselves.


def single_search(parent_class: type, name: str, case_sensitive: bool = False):
    """Finds a subclass of a parent class in the
    by searching the _registered_subclasses dictionary.

    Arguments:
        parent_class (type) -- a class with SubclassFactory metaclass
        name (str) -- name of the child class to be found

    Returns:
        A class (type) or None
    """
    for skey in parent_class._registered_subclasses.keys():
        if case_sensitive:
            lhand = skey
            rhand = name
        else:
            lhand = str(skey).lower()
            rhand = name.lower()
        if lhand == rhand:
            return parent_class._registered_subclasses[skey]

    return None


def recursive_search(parent_class: type, name: str):
    """Recursively searches _registered_subclasses dictionaries,
    allowing the parent class to find a subclass of a subclass as
    well as direct subclasses.

    Arguments:
        parent_class (type) -- a class with SubclassFactory metaclass
        name (str) -- name of the child class to be found

    Returns:
        A class (type) or None
    """
    return_type = single_search(parent_class, name)
    if return_type is not None:
        return return_type
    else:
        for child in parent_class._registered_subclasses.keys():
            return_type = recursive_search(
                parent_class._registered_subclasses[child], name
            )
            if return_type is not None:
                return return_type


def recursive_keys(parent_class: type) -> list:
    """Returns a list of class names of all the subclasses
    of a class created with SubclassFactory metaclass.
    This includes subclasses of subclasses.

    Arguments:
        parent_class (type) -- a class with SubclassFactory metaclass

    Returns:
        A list of class names (str)
    """
    try:
        results = parent_class.subclasses()
    except Exception:
        return []
    else:
        for child in parent_class.subclasses():
            results += recursive_keys(parent_class._registered_subclasses[child])
        return results


def recursive_dict(parent_class: type) -> dict:
    """Returns a dictionary of {str: type}
    of classes derived from the parent_class. The class name (str)
    is the key, and the class itself is a value.
    This way all the subclasses of a class built with SubclassFactory
    can be found, even if they are not _directly_ derived from
    the parent class.

    Arguments:
        parent_class (type) -- a class with SubclassFactory metaclass

    Returns:
        A dictionary {str: type} of class_name:class pairs
    """
    try:
        results = {
            ckey: parent_class._registered_subclasses[ckey]
            for ckey in parent_class.subclasses()
        }
    except Exception:
        return {}
    else:
        for child in parent_class.subclasses():
            newdict = recursive_dict(parent_class._registered_subclasses[child])
            results = {**results, **newdict}
        return results


class SubclassFactory(type):
    """A metaclass which gives a class the ability to keep track of
    its subclasses, and to work as a factory.
    """

    def __init__(cls, name, base, dct, **kwargs):
        super().__init__(name, base, dct)
        # Add the registry attribute to the each new child class.
        cls._registered_subclasses = {}

        @classmethod
        def __init_subclass__(cls, **kwargs):
            regkey = cls.__name__
            super().__init_subclass__(**kwargs)
            cls._registered_subclasses[regkey] = cls

        # Assign the nested classmethod to the "__init_subclass__" attribute
        # of each child class.
        # It isn't needed in the terminal children too.
        # May be there is a way to avoid adding these needless attributes
        # (registry, __init_subclass__) to there. I don't think about it yet.
        cls.__init_subclass__ = __init_subclass__

    def create(cls, name: str, *args, **kwargs) -> Self:
        """Finds the class called 'name' in the _registered_subclasses
        dictionary of the parent class, and returns an instance
        of that class with the *args, **kwargs passed to the constructor.

        Arguments:
            name (str) -- Name of the subclass to be created
            *args -- arguments for the subclass constructor
            **kwargs -- keyword arguments for the subclass constructor

        Returns:
            Self-type object - an instance of the requested class.
        """
        try:
            specific_class = cls._registered_subclasses[name]
        except KeyError:
            specific_class = recursive_search(cls, name)
        if specific_class is None:
            subclasses = [i.lower() for i in cls.indirect_subclasses()]
            closest = difflib.get_close_matches(name.lower(), subclasses)
            err_str = f"Could not find {name} in {cls.__name__}."
            if len(closest) > 0:
                err_str += f" Did you mean: {closest[0]}?"
            raise ValueError(err_str)
        return specific_class(*args, **kwargs)

    def subclasses(cls):
        """Returns a list of class names that are derived
        from this class.

        Returns:
            list(str) -- a list of the subclasses of this class
        """
        return list(cls._registered_subclasses.keys())

    def indirect_subclasses(cls):
        """Returns an extended list of class names that are derived
        from this class, including subclasses of subclasses

        Returns:
            list(str) -- a list of the subclasses of this class
        """
        return recursive_keys(cls)

    def indirect_subclass_dictionary(cls):
        """Returns a {name(str): class(type)} dictionary of classes derived
        from this class, including subclasses of subclasses.

        Returns:
            dict(str:type) -- a dictionary of the subclasses of this class
        """
        return recursive_dict(cls)
