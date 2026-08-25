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

from collections.abc import Callable, Iterable, KeysView, Mapping, ValuesView
from typing import Any, ClassVar, Generic, ParamSpec, TypeVar

from more_itertools import always_iterable

from MDANSE.IO.IOUtils import UCDict

P = ParamSpec("P")
T_co = TypeVar("T_co", bound="RegisterFactory", covariant=True)
T = TypeVar("T")

class RegisterFactory(Generic[T_co]):
    """
    Factory requiring manual registration to data.

    Attributes
    ----------
    registry : dict[str, type[T_co]]
        Dictionary of keys to names.

    See Also
    --------
    RegisterFactory.register : Registration mechanism.
    """

    registry: ClassVar[dict[str, type[Any]]]

    @classmethod
    def instance(cls, key: str) -> type[T_co]:
        """
        Return a callable instance to construct given class.
        """
        return cls.registry[key]

    @classmethod
    def create(cls, key: str, *args: P.args, **kwargs: P.kwargs) -> T_co:
        """
        Return an instance of given class.
        """
        return cls.instance(key)(*args, **kwargs)

    @classmethod
    def available_names(cls) -> KeysView[str]:
        """
        Known names supported by factory.

        Returns
        -------
        ~collections.abc.KeysView[str]
            Available keys to load.
        """
        return cls.registry.keys()

    @classmethod
    def raw_dict(cls) -> dict[str, type[T_co]]:
        """
        Get raw name dictionary.

        Returns
        -------
        ~dict[str, type[T]]
            Available keys to load.

        Notes
        -----
        Only available on cases where registry is UCDict.
        """
        if isinstance(cls.registry, UCDict):
            return cls.registry.raw_dict
        return cls.registry

    @classmethod
    def raw_names(cls) -> Iterable[str]:
        """
        Get raw names of classes.

        Returns
        -------
        ~collections.abc.ValuesView[str]
            Available keys to load.

        Notes
        -----
        Only available on cases where registry is UCDict.
        """
        if isinstance(cls.registry, UCDict):
            return cls.registry.raw_mapping.values()
        return cls.registry.keys()

    @classmethod
    def available_classes(cls) -> set[type[T_co]]:
        """
        Known classes supported by factory.

        Returns
        -------
        set[type[T]]
            Available classes to load.
        """
        return set(cls.registry.values())

    @classmethod
    def registered(cls):
        return cls.registry.copy()

    @classmethod
    def register(cls, names: str | Iterable[str]) -> Callable[[type[T]], type[T]]:
        """
        A class level decorator for registering classes.

        The names of the modules with which the class is registered
        should be the parameter passed to the decorator.

        Parameters
        ----------
        names : str
            The names of the modules with are registered

        Example
        -------
        To register the ``SphericalQVectors`` class with ``IQVectors``:

        .. code-block:: python

            class IQVectors(RegisterFactory["IQVectors"]): ...

            @IQVectors.register('SphericalQVectors')
            class SphericalQVectors(Observable): ...
        """

        def class_wrapper(wrapped_class: type[T]) -> type[T]:
            for name in always_iterable(names):
                if name in cls.registry:
                    raise KeyError(
                        f"{name!r} already in registry. Over-riding registry is forbidden."
                    )
                cls.registry[name] = wrapped_class
            return wrapped_class

        return class_wrapper
