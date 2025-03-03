from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from MDANSE.Core.Error import Error

SENTINEL = object()
T = TypeVar("T")


class ConfigError(Error):
    pass

class ConfigureDescriptor(ABC, Generic[T]):

    _old_name = "Invalid"

    def __init__(self,
                 *,
                 root: str = None,
                 dependencies: dict = None,
                 default: Any = SENTINEL,
                 widget: type = None,
                 label: str = None,
                 **parameters):
        self.root = root
        self.dependencies = dependencies if dependencies else {}
        self.default = default
        self.widget = widget if widget else type(self)
        self.optional = default is not SENTINEL
        self.configured = False
        self.value = default if self.optional else None

    def __set_name__(self, owner, name):
        if not hasattr(owner, "settings"):
            owner.settings = {}
        owner.settings[name] = (self._old_name, self.__dict__.copy())
        self.name = name

    def __get__(self, owner, objtype=None) -> T:
        if not self.configured:
            if self.optional:
                return self.default
            else:
                raise ValueError(f"Mandatory parameter {self.name!r} not configured")
        elif owner._configuration[self.name]["value"] != self.value:
            ...

        return owner._configuration[self.name]["value"]

    def __set__(self, owner, value):
        self.value = self.validate(value)
        self.configured = True
        owner._configuration[self.name]["value"] = self.value

    @abstractmethod
    def validate(self, value) -> T:
        """
        Ensure that the passed variable is of the right type.
        """
        raise NotImplementedError()
