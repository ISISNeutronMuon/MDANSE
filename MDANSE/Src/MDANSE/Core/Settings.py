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

import copy
from collections import ChainMap, UserDict, defaultdict
from collections.abc import Callable, Generator, Mapping
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Any, ClassVar, Generic, NamedTuple, TypeAlias, TypeVar

import tomlkit
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile

from MDANSE.MLogging import LOG

T = TypeVar("T")
X = TypeVar("X")


# 3.11+, Generic[T]
class Option(NamedTuple):
    """Tuple defining a specialised option."""

    value: T
    name: str = ""
    group: str = ""
    comment: str | None = None
    visible: bool = True


NULLOPTION = Option(None)


SettingsDict: TypeAlias = dict[str, dict[str, Option]]
SettingsRaw: TypeAlias = Mapping[str, Mapping[str, Any]]


class Settings:
    """Singleton class which settings.

    It contains two paired dictionaries (_settings, _defaults), in which
    the settings are defined.

    :attr:`_defaults` is the static underlying set of definitions.
    :attr:`_settings` is the dynamic set of user-specified definitions.

    Parameters
    ----------
    settings : Path, optional
        Path to initial settings/defaults.
    save : bool
        Whether updates should be saved by default.

    Attributes
    ----------
    settings : The public interface; defines a Mapping[str, ChainMap(_settings, _defaults)]
        style interface so updates to settings are
        recorded in _settings and _defaults is left untouched.
    _settings : dynamic and contains the custom settings which are saved
    _defaults : should mostly be static and values in _defaults are not saved (they are assumed to be inferred).
    """

    class _SettingsDict(dict[str, ChainMap[str, Option]]):
        """Settings dict to create mappings if not defined."""

        def __missing__(self, key: str):
            self[key] = ChainMap(Settings._settings[key], Settings._defaults[key])
            return self[key]

        def __contains__(self, key) -> bool:
            self._reup()
            return super().__contains__(key)

        def _reup(self) -> None:
            for key in Settings._settings.keys() | Settings._defaults.keys():
                self[key]

        def __repr__(self) -> str:
            self._reup()
            return super().__repr__()

    auto_save: ClassVar[bool] = False
    settings: ClassVar[_SettingsDict] = _SettingsDict()
    _defaults: ClassVar[SettingsDict] = defaultdict(dict)
    _settings: ClassVar[SettingsDict] = defaultdict(dict)
    _filename: ClassVar[Path | None] = None
    _parameters: ClassVar[set[Option]] = {
        Option(str(Path.home()), "path", "path", "Default path for search start."),
        Option("meV", "energy", "units", "The unit of energy preferred by the user."),
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
    }

    @classmethod
    def __call__(cls):
        return cls

    def __init__(self, *_, **__):
        raise NotImplementedError("Cannot instantiate Settings")

    def __init_subclass__(cls, *_, **__):
        raise NotImplementedError("Cannot subclass Settings")

    @classmethod
    def init(
        cls,
        settings: Path | SettingsRaw | None = None,
        *,
        save: bool = True,
        clear: bool = True,
    ) -> None:
        if clear:
            cls.clear()
        cls.auto_save = save

        # Global settings
        for default in cls._parameters:
            cls.set_item(default)

        cls.load(settings)
        cls._init_dicts(cls._defaults, cls._settings)

    @classmethod
    def _init_dicts(cls, defaults: SettingsDict, settings: SettingsDict):
        cls._defaults = defaults
        cls._settings = settings
        cls.settings = cls._SettingsDict(
            {
                key: ChainMap(settings[key], defaults[key])
                for key in settings.keys() | defaults.keys()
            },
        )

    @classmethod
    def save(cls, filename: Path | None = None) -> None:
        """Save data to file.

        Parameters
        ----------
        filename : Path, optional
            Path to save, if not given overwrite place
            data loaded from.

        Raises
        ------
        ValueError
            If invalid filename provided.

        Notes
        -----
        If no filename given will save to place data loaded
        from. If not auto_save, this will not save.

        If a filename is given, it will always save, but not
        reload from this path.
        """
        if not cls.auto_save and filename is None:
            return

        filename = filename or cls._filename
        if not filename:
            raise ValueError(f"Cannot save to {filename}.")

        LOG.debug("Saving settings to %s", filename)
        cls.save_toml(filename)

    @classmethod
    def as_toml(cls) -> tomlkit.TOMLDocument:
        """Build a toml file and save to file.

        Returns
        -------
        tomlkit.TOMLDocument
            TOML document of settings.
        """
        newdoc = tomlkit.document()

        LOG.debug("Building TOML")

        for grp_key, grp in cls._settings.items():
            if not grp:
                continue

            table = tomlkit.table()

            LOG.debug("Group: %s", grp_key)
            for key, val in grp.items():
                item = tomlkit.item(val.value)
                if val.comment is not None:
                    item.comment(val.comment)
                table[key] = item
                LOG.debug("Elem (%s) = %s  # %s", key, val.value, val.comment)

            newdoc.add(grp_key, table)

        return newdoc

    @classmethod
    def save_toml(cls, filename: Path) -> None:
        """Save settings as TOML.

        Parameters
        ----------
        filename : Path
            Path to save to.
        """
        newdoc = cls.as_toml()
        file = TOMLFile(filename)
        file.write(newdoc)

    @classmethod
    def load(cls, settings: Path | SettingsRaw | None) -> None:
        """Load data from file or dict (and assign _filename).

        Parameters
        ----------
        settings : Path | SettingsRaw, optional
            Place to laod data from.
        """
        match settings:
            case None | Mapping():
                cls._filename = None
            case Path():
                cls._filename = settings

        cls._settings = cls._process(settings)

    @classmethod
    def _process(cls, settings: Path | SettingsRaw | None) -> SettingsDict:
        out = defaultdict(dict)

        match settings:
            case None:
                return out
            case Path():
                try:
                    data = TOMLFile(settings).read()
                except FileNotFoundError:
                    LOG.warning(f"File {settings} does not exist.")
                    return out
                except ParseError:
                    LOG.warning(f"File {settings} could not be parsed.")
                    return out
            case Mapping():
                data = settings
            case _:
                LOG.warning(f"Cannot parse {settings!r} as settings.")
                return out

        for grp_key, grp in data.items():
            for val_key, val in grp.items():
                LOG.debug("Init %s.%s=%s", grp_key, val_key, val)

                if hasattr(val, "trivia"):
                    comment = val.trivia.comment.removeprefix("# ")
                else:  # Take from defaults.
                    comment = (
                        cls._defaults.get(grp_key, {}).get(val_key, NULLOPTION).comment
                    )

                out[grp_key][val_key] = cls._process_val(
                    val_key, grp_key, val, add_comment=comment
                )

        return out

    @staticmethod
    def _process_val(
        key: str, grp_key: str, val: Option[T] | T, *, add_comment: str | None = None
    ) -> Option[T]:
        """Return Option from either value or Option."""
        match val:
            case Option(value, name, group, comment, visible):
                return Option(
                    value,
                    name or key,
                    group=group or grp_key,
                    comment=comment or add_comment,
                    visible=visible,
                )
            case _:
                return Option(val, key, grp_key, comment=add_comment)

    @classmethod
    def _get_opt(cls, _, grp: str, key: str) -> T:
        return cls.settings[grp][key].value

    @classmethod
    def _set_opt(cls, _, value: T, grp: str, key: str) -> None:
        cls.settings[grp].setdefault(key, Option(value, key, grp))
        LOG.debug("Setting %s.%s=%s", grp, key, value)

        cls.settings[grp][key] = cls.settings[grp][key]._replace(value=value)

    @classmethod
    def get_default(cls, grp: str, key: str) -> T:
        return cls._defaults[grp][key].value

    @classmethod
    def get_opt_w_default(
        cls, grp: str, key: str, default: T, comment: str | None = None
    ) -> Any:
        """Get value and if not present create one in "_defaults".

        Parameters
        ----------
        grp : str
            Group containing setting.
        key : str
            Setting key.
        default : T
            Default value to use.
        comment : str, optional
            Comment to apply to default.

        Returns
        -------
        T
            Value of setting.
        """
        if key not in cls.settings[grp]:
            cls.set_item(Option(default, key, grp, comment=comment))
        return cls.get_opt(grp, key)

    @classmethod
    def get_opt(cls, grp: str, key: str) -> T:
        """Get the value of a setting.

        Parameters
        ----------
        grp : str
            Group containing setting.
        key : str
            Setting key.

        Returns
        -------
        T
            Value of parameter.
        """
        return cls._get_opt(None, grp, key)

    @classmethod
    def set_opt(cls, grp: str, key: str, value: T) -> None:
        """Set the value of a setting, creating it if not defined.

        Parameters
        ----------
        grp : str
            Group containing setting.
        key : str
            Setting key.
        value : T
            Value to assign.
        """
        cls._set_opt(None, value, grp, key)

    @classmethod
    def set_item(cls, item: Option[T]) -> None:
        """Dynamically create a new default from an :ref:`Option`.

        Parameters
        ----------
        item : Option[T]
            Default to create.
        """
        cls._defaults.setdefault(item.group, {})
        cls._defaults[item.group][item.name] = item
        LOG.debug("Default %s.%s=%s", item.group, item.name, item.value)

    @classmethod
    def contains(cls, grp: str, key: str | None = None) -> bool:
        if key is None:
            return grp in cls.settings

        return grp in cls.settings and key in cls.settings[grp]

    @classmethod
    def clear(cls, *, clear_all: bool = False) -> None:
        """Clear all stored parameters.

        Parameters
        ----------
        all : bool
            Clear everything, including parameters.

        """
        cls._filename = None
        for key in cls._defaults.keys() | cls._settings.keys():
            cls._defaults[key].clear()
            cls._settings[key].clear()

        cls._defaults.clear()
        cls._settings.clear()
        cls.settings.clear()

        if clear_all:
            cls._parameters.clear()

    @classmethod
    def parametrise(cls, **kwargs: Option[T] | T) -> Callable[[type[X]], type[X]]:
        """Add settings to decorated class.

        For x = val, x will be the property on the class
        and can be accessed directly via . notation.

        Assigning to this value will update the value in Settings.

        If val is an :ref:`Option`, these settings should be defined there,
        if not provided or val is just a value they will be inferred as
        ``(Option(value=val, group=type(class).__name__, name=x, comment=None))``.

        Returns
        -------
        Callable[[type], type]
            Class decorator.

        Examples
        --------
        ..
            @Settings.parametrise(favourite=Option("pike", group="fish"))
            class Test:
                def __init__(self):
                    print(self.favourite) # => "pike"
                    self.favourite = "trout"
                    print(Settings.get_opt("fish", "favourite")) # "trout"
        """

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
                cls._parameters.add(value)

            return target

        return wrapped

    @staticmethod
    @contextmanager
    def temporary(**kwargs: Option[T] | T):
        with temp_settings(**kwargs):
            yield

    @classmethod
    def show(cls) -> str:
        return cls.as_toml().as_string()


@contextmanager
def temp_settings(**kwargs: Option[T] | T) -> Generator[None]:
    """Context manager for temporarily configuring settings.

    Upon exiting the `with` block, settings will be reverted.

    Auto-saving will not take place while in the block.
    """
    defaults = defaultdict(
        dict, **{key: copy.copy(val) for key, val in Settings._defaults.items()}
    )
    settings = defaultdict(
        dict, {key: copy.copy(val) for key, val in Settings._settings.items()}
    )
    filename = Settings._filename
    save = Settings.auto_save

    try:
        Settings.auto_save = False

        for key, val in kwargs.items():
            itm = Settings._process_val(key, "temp", val)
            Settings.set_item(itm)
            Settings.set_opt(itm.group, itm.name, itm.value)

        yield
    finally:
        Settings.auto_save = save
        Settings._init_dicts(defaults, settings)
        Settings._filename = filename
