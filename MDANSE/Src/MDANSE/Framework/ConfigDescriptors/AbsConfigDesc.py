from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Container, Iterator
from typing import Any, Generic, TypeVar

from MDANSE.Core.Error import Error

SENTINEL = object()
T = TypeVar("T")


class ConfigError(Error):
    pass


class ConfigureDescriptor(ABC, Generic[T]):
    """Abstract configure descriptor.

    Parameters
    ----------
    default : T
        Default value if not configured.
    optional : bool
        Whether this value can be disabled (None).
    choices : Container[T], optional
        Valid options for this value.
    exclude : Container[T]
        Invalid options for this value.
    mutex : Container[str]
        Other variables with which this is mutually exclusive.
    depends : Container[str]
        Other variables which must be set for this to be set.
    label : str
        GUI label to present to user.
    tooltip : str
        GUI tooltip to present to user.
    """

    def __init__(
        self,
        *,
        default: T = SENTINEL,
        optional: bool | None = None,
        choices: Container[T] | None = None,
        exclude: Container[T] = (),
        mutex: Container[str] = (),
        depends: Container[str] = (),
        label: str = "",
        tooltip: str = "",
    ):
        self.default: T = default
        self.optional = optional if optional is not None else default is not SENTINEL

        self.choices = choices
        self.exclude = exclude

        self.mutex = mutex
        self.depends = depends

        self.label = label
        self.tooltip = tooltip

        self.__doc__ = f"""\
{self.label}

{self.tooltip}
        """

    def __set_name__(self, owner: object, name: str):
        self.name = name
        self.private_name = "_" + name
        self.configured_var = self.private_name + "_configured"
        setattr(owner, self.configured_var, False)

    def __get__(self, owner: object, objtype: type | None = None) -> T:
        if owner is None:
            return self

        if not self.optional and not getattr(owner, self.configured_var):
            raise ConfigError(f"Non-optional value ({self.name}) has not been set")

        value = getattr(owner, self.private_name, SENTINEL)
        return value if value is not SENTINEL else self.default

    def _bad_mutex(self, owner: object) -> Iterator[bool]:
        return (getattr(owner, f"_{ex}_configured") for ex in self.mutex)

    def _bad_deps(self, owner: object) -> Iterator[bool]:
        return (not getattr(owner, f"_{dep}_configured") for dep in self.depends)

    def __set__(self, owner: object, value):
        setattr(owner, self.configured_var, False)
        setattr(owner, self.private_name, SENTINEL)

        if any(self._bad_deps(owner)):
            raise ConfigError(
                f"Dependencies ({', '.join(self._bad_deps)}) are not correctly defined."
            )
        if any(self._bad_mutex(owner)):
            raise ConfigError(
                f"Mutually exclusive value ({', '.join(self._bad_mutex)}) is also configured."
            )

        deps = {dep: getattr(owner, dep).value for dep in self.depends}

        setattr(owner, self.private_name, self.validate(value, deps))
        setattr(owner, self.configured_var, True)

    @property
    def choices(self) -> set[T]:
        """
        Returns the set of values allowed for an input.
        """
        return self._choices

    @choices.setter
    def choices(self, value: Container[T]) -> None:
        if value is None:
            self._choices = set()
            return
        self._choices = set(value)

    @property
    def exclude(self) -> set[int]:
        """
        Returns the set of values which are not forbidden.

        Returns
        -------
        set[int]
            Forbidden values.
        """
        return self._exclude

    @exclude.setter
    def exclude(self, value: Container[int]) -> None:
        if value is None:
            self._exclude = set()
            return
        self._exclude = set(value)

    def validate_choices(self, value: T) -> bool:
        return not self.choices or value in self.choices

    def validate_exclude(self, value: T) -> bool:
        return not self.exclude or value not in self.exclude

    @abstractmethod
    def validate(self, value: T, *_deps) -> T:
        """
        Ensure that the passed variable is of the right type.
        """
        if not self.validate_choices(value):
            raise ConfigError(
                f"Value ({value!r}) not in choices ({', '.join(self.choices)})."
            )

        if not self.validate_exclude(value):
            raise ConfigError(
                f"Value ({value!r}) in excluded values ({', '.join(self.exclude)})."
            )
