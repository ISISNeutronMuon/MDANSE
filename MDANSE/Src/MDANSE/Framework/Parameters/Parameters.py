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

import copy
import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from enum import Enum
from functools import singledispatchmethod
from itertools import compress
from textwrap import dedent, wrap
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    NamedTuple,
    Protocol,
    TypeGuard,
    cast,
    overload,
    runtime_checkable,
)

from more_itertools import first, first_true, partition, prepend, unzip, value_chain
from typing_extensions import Self, TypeVar

from MDANSE.Framework.Parameters.UtilTypes import (
    CB,
    Depends,
    DescID,
    K,
    Num,
    P,
    PredictionResult,
    T,
    V,
)
from MDANSE.IO.IOUtils import MDANSEEncoder, summarise_array
from MDANSE.MLogging import LOG

SENTINEL = object()

cjoin = ", ".join


class ParamInfo(NamedTuple):
    name: str
    default: Any
    description: str

    @staticmethod
    def wrap_desc(desc: str, *, width: int = 50) -> list[str]:
        """Line-wrap description into ``width`` chars.

        Parameters
        ----------
        desc : str
            String to wrap.
        width : int
            Max width.

        Returns
        -------
        list[str]
            Line-wrapped string.
        """
        return [
            blk
            for line in desc.splitlines()
            for blk in wrap(dedent(line), width=width, replace_whitespace=False)
        ]

    @property
    def description_wrapped(self) -> list[str]:
        """Description as list of lines max 50 (default) chars"""
        return self.wrap_desc(self.description)

    @property
    def description_summary(self) -> str:
        """Return summary line of description."""
        return first(self.description.strip().splitlines())

    @property
    def texttable_lengths(self) -> tuple[int, int, int]:
        """Return lengths of columns in texttable."""
        return len(self.name), len(str(self.default)), 50


@runtime_checkable
class Validatable(Protocol):
    """Protocol for checking whether type has validate method."""

    def validate(self, desc: ConfigureDescriptor, value: T) -> T: ...


@runtime_checkable
class CustomChoices(Protocol):
    """Protocol for checking whether type has choices method."""

    def get_choices(self, deps: Depends) -> set: ...


def is_enum(x: Any) -> TypeGuard[type[Enum]]:
    """Check whether object is an :class:`enum.Enum`.

    Parameters
    ----------
    x : Any
        Object to test.

    Returns
    -------
    TypeGuard[type[Enum]]
        Whether is :class:`enum.Enum`.
    """
    return isinstance(x, type) and issubclass(x, Enum)


class ConfigError(Exception):
    """Standard Error type for parameter configuration."""


class ConfigWarning(Warning):
    """Standard Warning type for parameter configuration."""


class Parameter:
    """
    Mixin for classes which can have a GUI Component.

    Parameters
    ----------
    label : str, optional
        GUI label.
    tooltip : str, optional
        GUI tooltip.
    optional_label : str, optional
        Label for optional check-box.
    """

    default_label = ""
    default_tooltip = ""

    # GUI compat
    optional = False

    def __init__(
        self,
        *,
        label: str | None = None,
        tooltip: str | None = None,
        optional_label: str | None = None,
        units: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.label = label or self.default_label
        self.tooltip = tooltip or self.default_tooltip
        self.optional_label = optional_label
        self.units = units
        if self.units:
            label = f"{self.label} ({self.units})"

        self.__doc__ = self.__doc__ or ""
        self.__doc__ += f"""
GUI Description
---------------
{self.label}

{self.tooltip}
        """

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        yield PredictionResult(self.label, value, self.units)


class Configurable:
    """Allows any object that derives from it to be configurable within the MDANSE framework.

    Parameters
    ----------
    **kwargs
        Default arguments.
    """

    def __init__(self, **kwargs: Any):
        if kwargs:
            self.configuration = kwargs

    @classmethod
    def _get_default_parameters(cls):
        """Get set of default parameters or "N/A" if no default."""
        return {
            key: desc.default
            if hasattr(desc, "default") and desc.has_default
            else "N/A"
            for key, desc in cls._get_descriptors().items()
        }

    default_parameters = property(lambda self: type(self)._get_default_parameters())

    @property
    def name(self) -> str:
        """Name for compatibility with ConfigureDescriptor.

        Returns
        -------
        str
            Class name.
        """
        return type(self).__name__

    def invalidate(self, owner: Configurable) -> None:
        """Mark self as invalid."""

    @property
    def configuration(self) -> dict[DescID, Any]:
        """Get/set parameters as dictionary.

        Compatibility layer with old ``Configurator`` classes.

        Returns
        -------
        dict[DescID, Any]
            Mapping of descriptor names to values.
        """

        return {name: getattr(self, name) for name in self.descriptors}

    @configuration.setter
    def configuration(self, value: dict[DescID, Any]):
        if extra := value.keys() - self.parameters:
            raise ConfigError(
                f"Unrecognised parameters in dict for {self.name}: {cjoin(extra)}."
            )

        # Preserve definition order
        for name in self.parameters:
            if name in value:
                setattr(self, name, value[name])

    @property
    def raw_values(self) -> dict[DescID, Any]:
        """Mapping of values as entered by user before validation.

        Returns
        -------
        dict[DescID, Any]
            Mapping of descriptor name to Values before validation.
        """
        return {
            name: (
                desc.raw_values
                if isinstance(desc, Configurable)
                else getattr(self, desc.raw_name)
            )
            for name, desc in self.descriptors.items()
        }

    @classmethod
    def _get_descriptors(cls) -> dict[DescID, Parameter]:
        """Get dictionary mapping keys to parameters.

        Returns
        -------
        dict[DescID, Parameter]
            Mapping of key to descriptor.
        """
        return {
            DescID(name): param
            for par in value_chain(cls.__bases__, cls)
            for name, param in par.__dict__.items()
            if isinstance(param, Parameter)
        }

    def __getstate__(self) -> dict[DescID, Any]:
        return self.raw_values

    def __setstate__(self, state: dict[DescID, Any]):
        obj, params = partition(self.parameters.__contains__, state)

        self.__dict__ = {key: state[key] for key in obj}
        self.configuration = {key: state[key] for key in params}

    descriptors = property(lambda self: type(self)._get_descriptors())

    @property
    def parameters(self) -> list[DescID]:
        """Parameter names as a list.

        Returns
        -------
        list[DescID]
            List of parameter names.
        """
        return list(self.descriptors)

    def to_json(self) -> str:
        """Mapping of self to JSON-compatible string.

        Returns
        -------
        str
            JSON-compatible string.
        """
        to_json = {
            name: obj.to_json() if isinstance(obj, Parameter) else {name: str(obj)}
            for name, obj in self.configuration.items()
        } | {"class_type": type(self).__name__}
        return json.dumps(to_json, cls=MDANSEEncoder)

    output_configuration = to_json

    def check_status(self) -> bool:
        """Check if configurable is completely defined.

        Returns
        -------
        bool
            Whether all components of configurable are defined.
        """
        try:
            for param in self.parameters:
                getattr(self, param)
        except ConfigError:
            return False

        return True

    @classmethod
    def build_doc_example(cls) -> str:
        """Build example line for GUI panel.

        Returns
        -------
        str
            Example configuration string.
        """
        line_start = "\n>>> "

        return f"""\
Examples
--------
>>> job = {cls.__name__}()
>>> {line_start.join(f"job.{k} = {v!r}" for k, v in cls._get_default_parameters().items())}
>>> job.run()\n
"""

    @classmethod
    def doc_info(cls) -> Iterable[ParamInfo]:
        return (
            ParamInfo(
                name,
                default,
                getattr(desc, "description", "") + "\n" + str(desc.__doc__),
            )
            for (name, desc), default in zip(
                cls._get_descriptors().items(),
                cls._get_default_parameters().values(),
                strict=True,
            )
        )

    @classmethod
    def build_doc_texttable(cls, doclist: Iterable[ParamInfo]) -> str:
        """Build a text table for documenting in GUI.

        Parameters
        ----------
        doclist : list[dict[str, str]]
            Params to process.

        Returns
        -------
        str
            Job table.
        """
        docstring = "**Job parameters:** \n\n"

        columns = ("Parameter", "Default value", "Description")

        size_iter = prepend(map(len, columns), (v.texttable_lengths for v in doclist))
        len_name, len_default, len_desc = unzip([(x, y, z) for x, y, z in size_iter])
        sizes = (max(len_name), max(len_default), max(len_desc))

        data_line = "| " + "| ".join(f"{{}}:<{size}" for size in sizes) + "|\n"
        sep_line = "+" + "+".join("-" * (size + 1) for size in sizes) + "+\n"

        docstring += sep_line
        docstring += data_line.format(*columns)
        docstring += sep_line.replace("-", "=")

        for v in doclist:
            desc, *remainder = v.description_wrapped
            docstring += data_line.format(v.name, v.default, desc)
            for descr in remainder:
                docstring += data_line.format("", "", descr)
            docstring += sep_line

        docstring += "\n"
        return docstring

    @staticmethod
    def wrap_html(content: str, style: str) -> str:
        return f"<{style}>{content}</{style}>"

    @staticmethod
    def to_html_row(row: Sequence[str], style: str) -> str:
        row_fmt = Configurable.wrap_html("{}", style)
        return "".join(map(row_fmt.format, row))

    @classmethod
    def build_doc_htmltable(cls, doclist: Iterable[ParamInfo]) -> str:
        docstring = "**Job input parameters:**\n"

        docstring = (
            cls.wrap_html(
                cls.to_html_row(("Parameter", "Default value", "Description"), "th"),
                "tr",
            )
            + "\n"
        )
        docstring += "\n".join(
            cls.wrap_html(
                cls.to_html_row((v.name, v.default, v.description_summary), "td"),
                "tr",
            )
            for v in doclist
        )
        return cls.wrap_html(docstring, "table")

    @classmethod
    def build_doc(cls, use_html_table: bool = False) -> str:
        """Return the documentation about a configurable class based on its configurators contents.

        Parameters
        ----------
        cls : Configurable
            The configurable class for which documentation should be built.
        use_html_table : bool
             Use an HTML table.

        Returns
        -------
        str
            The documentation about the configurable class.
        """
        docstring = cls.build_doc_example()

        func = cls.build_doc_htmltable if use_html_table else cls.build_doc_texttable

        return docstring + func(cls.doc_info())

    @property
    def invalid(self) -> Iterable[str]:
        for param in self.parameters:
            try:
                getattr(self, param)
            except ConfigError:
                yield param

    def __str__(self) -> str:
        out = f"{type(self).__name__}(\n"
        for param in self.parameters:
            try:
                val = getattr(self, param)
            except ConfigError:
                val = "Undefined or invalid"

            if not isinstance(val, str) and isinstance(val, Sequence):
                val = f"[{summarise_array(val)}]"

            out += f"  {param} = {val},\n"
        out += ")"
        return out


class HasDependencies:
    """Mixin for classes which support dependencies.

    Takes a list which maps an internal dependency name to
    a parameter on the parent object.

    When ``__get__`` or ``__set__`` are called on the parameter. These
    dependencies are obtained and passed through to validation
    functions as a dictionary of the internal name to the current
    value of the dependency.

    This class also handles checking whether dependencies are valid
    before attempting to use them and invalidating dependents if
    changes to a dependency render them so.

    Should a class require dependencies, these should be added to the
    :meth:`required_deps` method of that class, if an attempt to add a
    Parameter without all required dependencies is made an error will
    be raised.

    Parameters
    ----------
    depends : dict[str, DescID], optional
        Mapping of internal name to parameter on owner.
    """

    def __init__(self, *, depends: dict[str, DescID] | None = None, **kwargs):
        super().__init__(**kwargs)

        self.depends: dict[str, DescID] = depends if depends is not None else {}
        self.dependents: set[Configurable] = set()

        if missing := (self.required_deps() - self.depends.keys()):
            raise ConfigError(
                f"Required deps ({cjoin(missing)}) missing for {type(self).__name__}."
            )

    def _set_dependents(self, owner: object) -> None:
        """Mark self as dependent of its dependencies.

        Parameters
        ----------
        owner : object
            Parent object.
        """
        # Update the depend checks
        for dep in self.depends.values():
            if dep != "parent":
                owner.__dict__[dep].dependents.add(self)

    def _bad_deps(
        self, owner: object, depends: dict[str, DescID] | None = None
    ) -> Iterable[bool]:
        """Check that all dependencies are configured and available.

        Parameters
        ----------
        owner : object
            Parent object which contains the dependencies.
        depends : dict[str, DescID], optional
            Override for ``self.depends`` containing dependencies.

        Returns
        -------
        Iterable[bool]
            Iterable over which dependencies available.
        """
        deps = depends if depends is not None else self.depends
        return (
            not getattr(owner, f"_{dep}__configured", False)
            for dep in deps.values()
            if dep != "parent"
        )

    def _get_deps(
        self,
        owner: object,
        depends: dict[str, DescID] | None = None,
        parent: object = None,
    ) -> Depends:
        """Get the values of dependencies from owner.

        Parameters
        ----------
        owner : object
            Parent object.
        depends : dict[str, DescID], optional
            Override for ``self.depends`` containing dependencies.

        Returns
        -------
        Depends
            Mapping of dependency to value.

        Raises
        ------
        ConfigError
            Dependencies are invalid.
        """
        dependencies = depends if depends is not None else self.depends

        if any(self._bad_deps(owner, dependencies)):
            raise ConfigError(
                f"Dependencies ({cjoin(compress(dependencies, self._bad_deps(owner)))}) "
                "are not correctly defined."
            )

        dep_values = {
            dep: getattr(owner, key)
            for dep, key in dependencies.items()
            if key != "parent"
        }

        if "parent" in dependencies.values() and isinstance(owner, CustomConfig):
            dep_values |= {
                dep: owner.last_deps[dep]
                for dep, key in dependencies.items()
                if key == "parent"
            }

        return cast("Depends", dep_values)

    def required_deps(self) -> set[DescID]:
        return set()

    def _find_dep_class(self, typ: type[Configurable]) -> Configurable | None:
        return first_true(
            self.dependents,
            pred=lambda x: isinstance(x, typ),
        )

    def _validate_dependents(self, owner: Configurable):
        for dependent in self.dependents:
            name = dependent.name
            try:
                val = getattr(owner, name)
                setattr(owner, name, val)
            except ConfigError as err:
                if err.args and "Required" not in err.args[0]:
                    LOG.info(f"Invalidated {name!r}. Reason: {err}")
                    dependent.invalidate(owner)


class CustomConfig(Parameter, HasDependencies, Configurable):
    """Class which can contain ConfigureDescriptors, but are to be configured."""

    def __new__(cls, *args, **kwargs) -> type[Self]:
        if any(
            not isinstance(desc, ConfigureDescriptor)
            for desc in cls._get_descriptors().values()
        ):
            raise TypeError("Cannot nest CustomConfigs.")

        return super().__new__(cls)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._last_owner = None

    def __set_name__(self, _owner: type, name: str) -> None:
        self._name = name
        self.private_name = "_" + name + "_"

    @property
    def data_name(self) -> str:
        return self.private_name + "_data"

    @property
    def data(self) -> dict[DescID, Any]:
        return getattr(self.owner, self.data_name)

    @property
    def raw_name(self) -> str:
        return self.private_name + "_raw"

    @property
    def raw_values(self) -> dict[DescID, Any]:
        return getattr(self.owner, self.raw_name)

    @property
    def configured_name(self) -> str:
        return self.private_name + "_configured"

    @property
    def configured(self) -> dict[DescID, bool]:
        return getattr(self.owner, self.configured_name)

    @property
    def owner(self) -> Configurable:
        if self._last_owner is None:
            raise ConfigError("Owner undefined -- Called in exceptional manner")
        return self._last_owner

    @owner.setter
    def owner(self, owner: Configurable) -> None:
        self._last_owner = owner
        self._add_friends(owner)

    def _add_friends(self, owner) -> None:
        if hasattr(owner, self.data_name):
            return

        data = {}
        raw = {}
        configured = {}

        for name, desc in self.descriptors.items():
            data[name] = SENTINEL
            raw[name] = desc.default
            configured[name] = desc.has_default

        setattr(owner, self.data_name, data)
        setattr(owner, self.raw_name, raw)
        setattr(owner, self.configured_name, configured)

    @overload
    def __get__(self, owner: Configurable, objtype: type) -> Self: ...
    @overload
    def __get__(self, owner: Configurable, objtype: None) -> type[Self]: ...
    def __get__(self, owner: Configurable, objtype: type | None):
        self.owner = owner
        self.last_deps = self._get_deps(owner)
        return self

    def __set__(self, owner: Configurable, value):
        raise ConfigError(
            f"Do not know how to set ({type(self).__name__}) with ({type(value).__name__})"
        )

    def __getattribute__(self, name):
        descriptors = type(self)._get_descriptors()

        if name.endswith("_configured"):
            return self.configured[name.removesuffix("_configured").strip("_")]

        if name not in descriptors:
            return super().__getattribute__(name)

        name = DescID(name)
        desc: ConfigureDescriptor = descriptors[name]
        value = self.data[name]

        if desc.has_default and value is SENTINEL:
            deps = desc._get_deps(self)
            value = desc.validate(desc.default, deps)

        if desc.on_get is not None:
            cb_deps = desc._get_deps(self, desc.get_depends)
            out = desc.on_get(desc, value, cb_deps)
        else:
            out = value

        return out

    def __setattr__(self, name, value):
        if name not in self.parameters:
            return super().__setattr__(name, value)

        self.last_deps = self._get_deps(self.owner)
        self.configured[name] = False
        self.data[name] = SENTINEL
        desc: ConfigureDescriptor = self.descriptors[name]

        raw = value
        if desc.optional and value is None:
            return

        out = desc._verify_on_set(self, value)

        self.data[name] = out
        self.raw_values[name] = raw
        self.configured[name] = True

        desc._validate_dependents(self)


class ConfigureDescriptor(Parameter, HasDependencies, Generic[P, T, CB]):
    """Abstract configure descriptor.

    Parameters
    ----------
    default : P
        Default value if not configured.
    optional : bool
        Whether this value can be disabled (giving None in most cases).
    choices : Sequence[T], optional
        Valid options for this value.
    exclude : Sequence[T]
        Invalid options for this value.
    mutex : Sequence[str]
        Other variables with which this is mutually exclusive.
    depends : Sequence[str]
        Other variables which must be set for this to be set.
    on_set : Callable
        Custom function to be called post-validation.
    on_get : Callable
        Custom function to be called before returning value.
    label : str
        GUI label to present to user.
    tooltip : str
        GUI tooltip to present to user.
    """

    def __init__(
        self,
        *,
        default: P | object = SENTINEL,
        optional: bool = False,
        choices: Sequence[T] | type[Enum] | None = None,
        exclude: Sequence[T] = (),
        mutex: Sequence[DescID] = (),
        depends: dict[str, DescID] | None = None,
        on_set_depends: dict[str, DescID] | None = None,
        on_set: Callable[[Self, T, Depends], CB] | None = None,
        on_get_depends: dict[str, DescID] | None = None,
        on_get: Callable[[Self, T, Depends], CB] | None = None,
        label: str = "",
        tooltip: str = "",
        units: str = "",
        optional_label: str = "",
    ):
        self.default = default
        self.optional = optional

        if on_set and on_get:
            raise NotImplementedError("Cannot have both on_set and on_get specified")

        self.on_set = on_set
        self.on_get = on_get

        self.get_depends: dict[str, DescID] = on_get_depends or {}
        self.set_depends: dict[str, DescID] = on_set_depends or {}

        if optional and not self.has_default:
            raise ConfigError("Cannot be optional without default.")

        self.choices = choices
        self.exclude = exclude

        self.mutex = mutex

        super().__init__(
            depends=depends,
            label=label,
            tooltip=tooltip,
            optional_label=optional_label,
            units=units,
        )

    @property
    def has_default(self) -> bool:
        """Whether parameter has a defined default."""
        return self.default is not SENTINEL

    def _bad_mutex(self, owner: Configurable) -> Iterable[bool]:
        return (getattr(owner, f"_{ex}__configured") for ex in self.mutex)

    @property
    def configured_var(self) -> str:
        return self.private_name + "_configured"

    @property
    def raw_name(self) -> str:
        return self.private_name + "_raw"

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.private_name = "_" + name + "_"

        setattr(owner, self.configured_var, self.has_default)
        setattr(owner, self.raw_name, self.default)

        self._set_dependents(owner)

    @overload
    def __get__(self, owner: Configurable, objtype: type) -> CB: ...
    @overload
    def __get__(self, owner: None, objtype: None) -> Self: ...
    def __get__(
        self,
        owner: Configurable | None,
        objtype: type | None,
    ):
        if owner is None:
            return self

        if not self.has_default and not getattr(owner, self.configured_var):
            raise ConfigError(f"Required value ({self.name}) has not been set")

        value = getattr(owner, self.private_name, SENTINEL)

        if self.has_default and value is SENTINEL:
            deps = self._get_deps(owner)
            value = self.validate(cast("P", self.default), deps)

        if self.on_get is not None:
            cb_deps = self._get_deps(owner, self.get_depends)
            try:
                out = self.on_get(self, cast("T", value), cb_deps)
            except Exception as err:
                raise ConfigError(f"`on_get` failed: {err}") from err
        else:
            out = cast("CB", value)

        return out

    def __set__(self, owner: Configurable, value: P) -> None:
        setattr(owner, self.configured_var, self.has_default)
        setattr(owner, self.private_name, SENTINEL)
        raw = value

        if self.optional and value is None:
            return

        out = self._verify_on_set(owner, value)

        setattr(owner, self.private_name, out)
        setattr(owner, self.configured_var, True)
        setattr(owner, self.raw_name, raw)

        self._validate_dependents(owner)

    def _verify_on_set(self: Self, owner: Configurable, value: P) -> T | CB:
        if any(self._bad_mutex(owner)):
            raise ConfigError(
                f"Mutually exclusive value ({cjoin(compress(self.mutex, self._bad_mutex(owner)))}) "
                "is also configured."
            )

        deps = self._get_deps(owner)
        try:
            proc = self.validate(value, deps)
        except ConfigError:
            raise
        except Exception as err:
            raise ConfigError(f"`validate` failed: {err}") from err

        # For grouped config descriptors
        if isinstance(owner, Validatable):
            try:
                proc = owner.validate(self, proc)
            except ConfigError:
                raise
            except Exception as err:
                raise ConfigError(f"`validate` failed: {err}") from err

        # If callback
        if self.on_set is not None:
            cb_deps = self._get_deps(owner, self.set_depends)
            try:
                out = self.on_set(self, proc, cb_deps)
            except Exception as err:
                raise ConfigError(f"`on_set` failed: {err}") from err
        else:
            out = cast("CB", proc)

        return out

    @property
    def choices(self) -> set[T] | type[Enum]:
        """Returns the set of values allowed for an input.

        Returns
        -------
        set[T] | type[Enum]
            Valid choice containers.
        """
        if isinstance(self, CustomChoices):
            return self.last_choices

        return self._choices

    @choices.setter
    def choices(self, value: Sequence[T] | type[Enum] | None) -> None:
        self._choices: set[T] | type[Enum]
        if value is None:
            self._choices = set()
        elif is_enum(value):
            self._choices = value
        else:
            value = cast("Sequence[T]", value)
            self._choices = set(value)

        self.last_choices = self._choices

    @property
    def exclude(self) -> set[T]:
        """
        Returns the set of values which are forbidden.

        Returns
        -------
        set[int]
            Forbidden values.
        """
        return self._exclude

    @exclude.setter
    def exclude(self, value: Sequence[T] | None) -> None:
        self._exclude: set[T]
        if value is None:
            self._exclude = set()
            return
        self._exclude = set(value)

    def _validate_choices(self, value: T, choices: set[T] | None = None) -> bool:
        """Ensure that ``value`` is a valid choice.

        Parameters
        ----------
        value : T
            Value to test.
        choices : set[T], optional
            Override for choices.

            If not present, use ``self.choices``.

        Returns
        -------
        bool
            Whether choices are valid.
        """
        test_choices = self.choices if choices is None else choices
        return not test_choices or value in test_choices

    @singledispatchmethod
    def _validate_exclude(self, value: T, exclude: set[T] | None = None) -> bool:
        """Ensure that ``value`` is not excluded.

        Parameters
        ----------
        value : T
            Value to test.
        exclude : set[T], optional
            Override for exclude.

            If not present, use ``self.exclude``.

        Returns
        -------
        bool
            Whether value is permitted.
        """
        exclude = self.exclude if exclude is None else exclude
        return not exclude or value not in exclude

    @_validate_exclude.register(Sequence)
    def _(self, value: Sequence[T], exclude: set[T] | None = None) -> bool:
        excludes = self.exclude if exclude is None else exclude
        return set(value) > excludes

    @_validate_exclude.register(Mapping)
    def _(self, value: Mapping[K, V], exclude: set[K] | None = None) -> bool:
        excl = cast("set[K]", self.exclude if exclude is None else exclude)
        if erroneous := excl & value.keys():
            raise ConfigError(
                f"Forbidden keys ({cjoin(map(str, erroneous))}) are present."
            )
        return True

    @abstractmethod
    def validate(self, value: P, deps: Depends, /) -> T:
        """
        Ensure that the passed variable is of the right type.
        """
        # Assume that the variable is the right type at this point
        out = cast("T", value)

        # Choices
        if isinstance(self, CustomChoices):  # Function
            self.last_choices = self.get_choices(deps)

            if not self._validate_choices(out, self.last_choices):
                raise ConfigError(
                    f"Value ({out!r}) not in choices ({cjoin(map(str, self.last_choices))})."
                )

        elif self.choices and is_enum(self.choices):  # Enum
            try:
                out = self.choices(out)
            except ValueError:
                raise ConfigError(
                    f"Value ({out!r}) not in choices ({cjoin(choice.name for choice in self.choices)})."
                ) from None

        elif not self._validate_choices(out):  # Set
            if aliases := getattr(self, "aliases", {}):
                err_msg = f"Value ({out!r}) not in choices ({cjoin(map(str, self.choices))}) or aliases ({cjoin(map(str, aliases))})."
            else:
                err_msg = (
                    f"Value ({out!r}) not in choices ({cjoin(map(str, self.choices))})."
                )

            raise ConfigError(err_msg)

        # Exclude
        if not self._validate_exclude(out):
            raise ConfigError(
                f"Value ({out!r}) in excluded values ({cjoin(map(str, self.exclude))})."
            )

        return out

    def invalidate(self, owner: Configurable) -> None:
        """Mark self as invalid."""
        setattr(owner, self.configured_var, False)


def to_class(cls: Callable[[P], T]) -> Callable[Concatenate[Any, P, Any], T]:
    """Simplified wrapper for callbacks."""

    def tc(desc: Any, value: P, deps: Any) -> T:
        return cls(value)

    return tc


class MinMax(ABC, Generic[Num]):
    """Mixing allowing limits on numerical ranges."""

    def __init__(
        self,
        *args,
        minimum: Num | None = None,
        maximum: Num | None = None,
        **kwargs,
    ):
        self.minimum: Num | None = minimum
        self.maximum: Num | None = maximum
        super().__init__(*args, **kwargs)

    def get_ranges(self, deps: Depends) -> tuple[Num | None, Num | None]:
        """Get valid ranges.

        Parameters
        ----------
        deps : Depends
            Dependencies.

        Returns
        -------
        tuple[Num | None, Num | None]
            Minimum/maximum for the object.
        """
        return self.minimum, self.maximum

    def validate_range(
        self,
        value: Num,
        ranges: tuple[Num | None, Num | None] | None = None,
    ) -> None:
        """Check that the value meets the range constraints.

        Parameters
        ----------
        value : Num
            Value to test.
        ranges : tuple[Num | None, Num | None], optional
            Override for ranges to test.

            If not present, use ``self.minimum``, ``self.maximum``.

        Raises
        ------
        ConfigError
            If outside range.
        """
        if ranges is not None:
            mini, maxi = ranges
        else:
            mini, maxi = self.minimum, self.maximum

        try:
            self.validate_minimum(value, mini)
            self.validate_maximum(value, maxi)
        except ConfigError as err:
            raise ConfigError(
                f"Value ({value}) outside of valid range ({mini}, {maxi})"
            ) from err

    def validate_minimum(self, value: Num, mini: Num | None = None) -> None:
        """Check that value is above the minimum.

        Parameters
        ----------
        value : Num
            Value to test.
        mini : tuple[Num | None, Num | None], optional
            Override for minimum to test.

            If not present, use ``self.minimum``.

        Raises
        ------
        ConfigError
            If below minimum.
        """
        minimum = mini if mini is not None else self.minimum

        if minimum is None:
            return

        if value < minimum:
            raise ConfigError(f"Value ({value}) less than minimum ({minimum})")

    def validate_maximum(self, value: Num, maxi: Num | None = None) -> None:
        """Check that value is below the maximum.

        Parameters
        ----------
        value : Num
            Value to test.
        maxi : tuple[Num | None, Num | None], optional
            Override for maximum to test.

            If not present, use ``self.maximum``.

        Raises
        ------
        ConfigError
            If above maximum.
        """
        maximum = maxi if maxi is not None else self.maximum

        if maximum is None:
            return

        if value > maximum:
            raise ConfigError(f"Value ({value}) greater than maximum ({maximum})")
