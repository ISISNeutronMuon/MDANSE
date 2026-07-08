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

from collections import ChainMap, UserDict, defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, ClassVar, Generic, TypeAlias, TypeVar

import tomlkit
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile

from MDANSE.MLogging import LOG

T = TypeVar("T")


@dataclass
class Option(Generic[T]):
    """Tuple defining a specialised option."""

    value: T
    name: str = ""
    group: str = ""
    comment: str | None = None
    visible: bool = True

    def __post_init__(self) -> None:
        self._initialised = True

    def __setattr__(self, key: str, val: Any) -> None:
        if key != "value" and getattr(self, "_initialised", False):
            raise AttributeError(f"Attribute {key} is read-only")

        super().__setattr__(key, val)

    def new(self, value: T) -> Option[T]:
        return Option(value, self.name, self.group, self.comment, self.visible)


SettingsDict: TypeAlias = dict[str, dict[str, Option]]
SettingsRaw: TypeAlias = Mapping[str, Mapping[str, Any]]


class Settings:
    """Singleton class storing settings."""

    class _SettingsDict(dict[str, ChainMap[str, Option]]):
        """Settings dict to create mappings if not defined."""

        def __missing__(self, key):
            return ChainMap(Settings._settings[key], Settings._defaults[key])

    auto_save: ClassVar[bool] = False
    settings: ClassVar[_SettingsDict] = _SettingsDict()
    _defaults: ClassVar[SettingsDict] = defaultdict(dict)

    @classmethod
    def __call__(cls):
        return cls

    def __init__(self, *_, **__):
        raise NotImplementedError("Cannot instantiate Settings")

    def __init_subclass__(cls, *_, **__):
        raise NotImplementedError("Cannot subclass Settings")

    @classmethod
    def init(
        cls, settings: Path | SettingsRaw | None = None, *, save: bool = True
    ) -> None:
        # Global settings
        for default in (
            Option(str(Path.home()), "path", "path", "Default path for search start."),
            Option(
                "meV", "energy", "units", "The unit of energy preferred by the user."
            ),
            Option("fs", "time", "units", "The unit of time preferred by the user."),
            Option(
                "ang", "distance", "units", "The unit of distance preferred by the user"
            ),
            Option(
                "1/ang",
                "reciprocal",
                "units",
                "The momentum (transfer) unit preferred by the user",
            ),
        ):
            cls.set_item(default)

        cls.load(settings)
        cls.auto_save = save
        cls.settings = cls._SettingsDict(
            {
                key: ChainMap(cls._settings[key], cls._defaults[key])
                for key in cls._settings.keys() | cls._defaults.keys()
            },
        )

    @classmethod
    def save(cls, filename: Path | None = None) -> None:
        if not cls.auto_save and filename is None:
            return

        filename = filename or cls._filename
        if not filename:
            raise ValueError(f"Cannot save to {filename}.")

        LOG.debug("Saving settings to %s", filename)
        cls.save_toml(filename)

    @classmethod
    def save_toml(cls, filename: Path) -> None:
        newdoc = tomlkit.document()

        LOG.debug("Building TOML")

        for grp_key, grp in cls._settings.items():
            if not grp:
                continue

            table = tomlkit.table()

            LOG.debug("Group: %s", grp_key)
            for key, val in grp.items():
                table[key] = tomlkit.item(val.value)
                if val.comment is not None:
                    table[key].comment(val.comment)
                LOG.debug("Elem (%s) = %s  # %s", key, val.value, val.comment)

            newdoc.add(grp_key, table)

        file = TOMLFile(filename)
        file.write(newdoc)

    @classmethod
    def load(cls, settings: Path | SettingsRaw | None) -> None:
        match settings:
            case None | Mapping():
                cls._filename = None
            case Path():
                cls._filename = settings

        cls._settings = cls._process(settings)

    @classmethod
    def _process(cls, settings: Path | SettingsRaw | None) -> SettingsDict:
        match settings:
            case None:
                return {}
            case Path():
                try:
                    file = TOMLFile(settings).read()
                except FileNotFoundError:
                    LOG.warning(f"File {settings} does not exist.")
                    return defaultdict(dict)
                except ParseError:
                    LOG.warning(f"File {settings} could not be parsed.")
                    return defaultdict(dict)

                return defaultdict(
                    dict,
                    **{
                        grp_key: {
                            val_key: cls._process_val(val_key, grp_key, val)
                            for val_key, val in grp.items()
                        }
                        for grp_key, grp in file.items()
                    },
                )
            case Mapping():
                return defaultdict(
                    dict,
                    **{
                        grp_key: {
                            val_key: cls._process_val(val_key, grp_key, val)
                            for val_key, val in grp.items()
                        }
                        for grp_key, grp in settings.items()
                    },
                )
            case _:
                LOG.warning(f"Cannot parse {settings!r} as settings.")
                return {}

    @staticmethod
    def _process_val(key: str, targ_key: str, val: Option[T] | T) -> Option[T]:
        match val:
            case Option(value, name, group, comment):
                return Option(
                    value,
                    name or key,
                    group=group or targ_key,
                    comment=comment,
                )
            case _:
                return Option(
                    val,
                    key,
                    targ_key,
                )

    @classmethod
    def _get_opt(cls, _, grp: str, key: str) -> T:
        return cls.settings[grp][key].value

    @classmethod
    def _set_opt(cls, _, value: T, grp: str, key: str) -> None:
        cls.settings[grp].setdefault(key, Option(value, key, grp))
        LOG.debug("Setting %s.%s=%s", grp, key, value)

        cls.settings[grp][key] = cls.settings[grp][key].new(value)

    @classmethod
    def get_default(cls, grp: str, key: str) -> T:
        return cls._defaults[grp][key].value

    @classmethod
    def get_opt_w_default(
        cls, grp: str, key: str, default: T, comment: str | None = None
    ) -> T:
        if key not in cls.settings[grp]:
            cls.set_item(Option(default, key, grp, comment=comment))
        return cls.get_opt(grp, key)

    @classmethod
    def get_opt(cls, grp: str, key: str) -> T:
        return cls._get_opt(None, grp, key)

    @classmethod
    def set_opt(cls, grp: str, key: str, value: T) -> None:
        cls._set_opt(None, value, grp, key)

    @classmethod
    def set_item(cls, item: Option[T]) -> None:
        cls._defaults.setdefault(item.group, {})
        cls._defaults[item.group][item.name] = item
        LOG.debug("Default %s.%s=%s", item.group, item.name, item.value)

    @classmethod
    def parametrise(cls, **kwargs: Option[T] | T) -> Callable[[type], type]:
        """Add settings to decorated class."""

        def wrapped(target: type) -> type:
            targ_key = target.__name__

            for key, val in kwargs.items():
                value = cls._process_val(key, targ_key, val)

                setattr(
                    target,
                    key,
                    property(
                        partial(cls._get_opt, grp=value.group, key=value.name),
                        partial(cls._set_opt, grp=value.group, key=value.name),
                        doc=value.comment,
                    ),
                )
                cls.set_item(value)

            return target

        return wrapped
