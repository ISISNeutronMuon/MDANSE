from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Container, Set
from typing import Any, Generic, TypeVar

from MDANSE.Core.Error import Error

SENTINEL = object()
T = TypeVar("T")


class ConfigError(Error):
    pass

class ConfigureDescriptor(ABC, Generic[T]):
    def __init__(self,
                 *,
                 root: str = None,
                 dependencies: dict = None,
                 default: T = SENTINEL,
                 optional: bool = False,
                 label: str = "",
                 choices: Container[T] | None = None,
                 exclude: Container[T] = (),
                 mutex: Container[str] = (),
                 depends: Container[str] = (),
                 **parameters):
        self.root = root
        self.dependencies = dependencies if dependencies else {}
        self.default = default
        self.optional = optional
        self.choices = choices
        self.exclude = exclude
        self.mutex = mutex
        self.depends = depends
        self.configured = False

    def __set_name__(self, owner, name):
        self.name = name

    @property
    def value(self):
        if not self.optional and not self.configured:
            raise ConfigError("Non-optional value has not been set")

        return self.default if self.default is not SENTINEL else self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __get__(self, owner, objtype=None) -> T:
        return self.value

    @property
    def _bad_mutex(self, owner):
        return (getattr(owner, ex).configured for ex in self.mutex)

    @property
    def _bad_deps(self, owner):
        return (not getattr(owner, dep).configured for dep in self.depends)

    def __set__(self, owner, value):
        self.configured = False

        if any(self._bad_deps):
            raise ConfigError(f"Dependencies ({', '.join(self._bad_deps)}) are not correctly defined.")
        if any(self._bad_mutex):
            raise ConfigError(f"Mutually exclusive value ({', '.join(self._bad_mutex)}) is also configured.")

        deps = {dep: getattr(owner, dep).value for dep in self.depends}

        self.value = self.validate(value, deps)
        self.configured = True

    @property
    def choices(self) -> Set[T]:
        """
        Returns the set of values allowed for an input.
        """
        return self._choices

    @choices.setter
    def choices(self, value: Container[T]):
        if value is None:
            self._choices = []
        self._choices = set(value)

    @property
    def exclude(self) -> Set[int]:
        """
        Returns the set of values which are not forbidden.

        Returns
        -------
        Set[int]
            Forbidden values.
        """
        return self._exclude

    @exclude.setter
    def exclude(self, value: Container[int]):
        if value is None:
            self._exclude = []
        self._exclude = set(value)

    def validate_choices(self, value):
        return self.choices is not None and value in self.choices

    def validate_exclude(self, value):
        return self.exclude and value not in self.exclude

    @abstractmethod
    def validate(self, value, *_deps) -> T:
        """
        Ensure that the passed variable is of the right type.
        """
        if not self.validate_choices(value):
            raise ConfigError(f"Value ({value}) not in choices ({self.choices!r}).")

        if not self.validate_exclude(value):
            raise ConfigError(f"Value ({value}) in excluded values ({self.exclude!r}).")
