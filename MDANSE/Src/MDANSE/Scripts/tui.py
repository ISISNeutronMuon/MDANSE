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

# ruff: file-ignore[T201, PLR0911]
from __future__ import annotations
from MDANSE.Core.Platform import PLATFORM

import cmd
import csv
import sys
from argparse import Namespace
from collections.abc import Callable, Iterable, Sequence
from difflib import get_close_matches
from itertools import islice
from operator import itemgetter
from pathlib import Path, PurePath
from typing import cast

from more_itertools import split_before, value_chain

from MDANSE.Framework.AtomSelector.selection_builder import (
    OperationType,
    SelectionBuilder,
)
from MDANSE.Framework.Configurable import ConfigurationError
from MDANSE.Framework.Configurators import (
    HDFTrajectoryConfigurator,
    IConfigurator,
    MultiInputFileConfigurator,
    OutputFilesConfigurator,
    OutputTrajectoryConfigurator,
)
from MDANSE.Framework.Configurators.FileWithAtomDataConfigurator import (
    FileWithAtomDataConfigurator,
)
from MDANSE.Framework.Converters import Converter
from MDANSE.Framework.Jobs import IJob
from MDANSE.IO.IOUtils import tabulate
from MDANSE.MolecularDynamics.Trajectory import (
    Trajectory,
    chemical_system_summary,
    trajectory_summary,
)
from MDANSE.Results.MDAFile import MDAFile
from MDANSE.Scripts.funcs import (
    execute_analysis,
    execute_converter,
    execute_element,
)
from MDANSE.util_types import FloatArray

try:
    import readline
except ImportError:
    readline = None

try:
    import matplotlib.pyplot as mpl

    matplotlib_available = True
except ImportError:
    matplotlib_available = False


if sys.version_info < (3, 15):
    from types import MappingProxyType as frozendict

OPS_MAP = frozendict(
    {
        "=": OperationType.SET,
        "SET": OperationType.SET,
        "&": OperationType.INTERSECTION,
        "+": OperationType.UNION,
        "|": OperationType.UNION,
        "UNION": OperationType.UNION,
        "ADD": OperationType.UNION,
        "-": OperationType.DIFFERENCE,
        "DIFF": OperationType.DIFFERENCE,
        "DIFFERENCE": OperationType.DIFFERENCE,
    }
)

VALID_PROPS = frozendict(
    {
        alias: prop
        for prop, aliases in {
            "charge": ("charge", "q"),
            "fractional_coordinates": (
                "fractional_coordinates",
                "frac",
                "fractional",
                "frac_coords",
            ),
            "coordinates": (
                "coordinates",
                "abs",
                "absolute",
                "pos",
                "position",
                "coords",
            ),
            "types": ("types", "species", "spec"),
            "index": ("index", "indices", "ind"),
            "name": ("name", "names", "label", "labels"),
            "cluster": ("cluster", "groups"),
            "molecule": ("molecule", "mol"),
            "dummy": ("dummy",),
        }.items()
        for alias in aliases
    }
)
PROP_TYPES = frozendict(
    {
        "charge": float,
        "fractional_coordinates": (float, float, float),
        "coordinates": (float, float, float),
        "types": str,
        "index": int,
        "name": str,
        "cluster": str,
        "molecule": str,
        "dummy": bool,
    }
)
PROPS = frozenset(VALID_PROPS)
CONVERTERS = tuple(Converter.registry.raw_mapping.values())
ANALYSES = tuple(IJob.registry.raw_mapping.values())


def parse(line: str) -> list[str]:
    return line.split()


def _list_type(in_list: list[str], typ: type) -> bool:
    try:
        [typ(x) for x in in_list]
    except Exception:
        return False
    else:
        return True


class MDANSETui(cmd.Cmd):
    """MDANSE TUI (Text User-interface) controller."""

    intro = "Welcome to the MDANSE TUI. Type help or ? to list commands.\n"
    #: This is the template which governs how the prompt is displayed.
    PROMPT_TEMPLATE = "mdanse{traj}{frame}{analysis}{charge}{trans} > "
    DEFAULT_TABLE = 20
    prompt = "mdanse > "
    identchars = cmd.IDENTCHARS + "/"
    hist_file_size = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.builder = SelectionBuilder()
        self.trajectory: Trajectory | None = None
        self.results: MDAFile | None = None
        self.atom_alias: dict[str, str] | None = None
        self.partial_charge: dict[str, list[int]] | None = None
        self.frame: int = 0
        self._update_prompt()

    @property
    def _hist_file(self) -> Path:
        return PLATFORM.application_directory / "tui_hist"

    def emptyline(self): ...

    def _update_prompt(self) -> None:
        self.prompt = self.PROMPT_TEMPLATE.format(
            traj=f" Traj:{Path(self.trajectory.filename).name}"
            if self.trajectory is not None
            else "",
            frame=f"({self.frame})" if self.frame else "",
            analysis=f" Res:{Path(self.results.filename).name}"
            if self.results is not None
            else "",
            charge=" Charge:True" if self.partial_charge is not None else "",
            trans=" Alias:True" if self.atom_alias is not None else "",
        )

    def _info(self, *args, **kwargs):
        print(*args, **kwargs, file=self.stdout)

    def _display(self, line: str, *args, **kwargs):
        """Print while not destroying prompt."""
        self._info("\n", *args, **kwargs)
        self.stdout.flush()

        self._info(f"{self.prompt}{line}", end="", **kwargs)
        self.stdout.flush()

    def _fail(self, cause: str, caller: str = ""):
        self._info(cause)
        if caller:
            self._info()
            self.do_help(caller)

    def preloop(self):
        if readline and self._hist_file.is_file():
            readline.read_history_file(self._hist_file)

    def postloop(self):
        if readline:
            readline.set_history_length(self.hist_file_size)
            readline.write_history_file(self._hist_file)

    def cmdloop(self, *_):
        super().cmdloop()

    @staticmethod
    def fuzzy_complete(curr: str, words: Iterable[str]) -> list[str]:
        """Attempt to complete phrase.

        If the text starts any of the potential words this list
        will be returned.

        Otherwise it will try to see if any words in the list may be typoed
        and return that list (max 3).

        Parameters
        ----------
        curr : str
            Current text entered.
        words : Iterable[str]
            Potential keywords which may be matched.

        Returns
        -------
        list[str]
            Potential matches.
        """
        if possible := [word for word in words if word.startswith(curr)]:
            return possible
        return get_close_matches(curr, words, cutoff=0.1)

    def results_match(self, text: str) -> list[str]:
        """Get paths matching paths from results.

        Parameters
        ----------
        results : MDAFile
            File to check.
        text : str


        Returns
        -------
        list[str]
            FIXME: Add docs.

        Examples
        --------
        FIXME: Add docs.

        """
        if self.results is None:
            self._info("\nNo results, try '?results'")
            return []

        path = PurePath(text)

        if text.endswith("/"):
            base, file = text, ""
        else:
            base, file = path.parent, path.name

        base = PurePath(base)
        self._display("results print "+text, f"{base=}, {file=}")
        return [
            str(pth.relative_to(base))[len(file):]
            for pth in self.results.all_dataset_paths
            if str(pth).startswith(str(base / file))
        ]

    @staticmethod
    def path_match(text: str) -> list[str]:
        """Get next parameter from path matching.

        By default this will search from the CWD.

        If text represents a directory an extra completion
        will insert a trailing "/"

        Parameters
        ----------
        text : str
            Existing text.

        Returns
        -------
        list[str]
            Potentially matching paths.
        """
        path = Path(text)

        if text and path.is_dir() and not text.endswith("/"):
            return [f"{path.name}/"]
        if text.endswith("/"):
            base, file = text, ""
        else:
            base, file = path.parent, path.name

        base = Path(base)
        return [str(pth.relative_to(base)) for pth in base.glob(file + "*")]

    def pprint_system(
        self,
        frame: int = 0,
        *,
        selection: Sequence[int] = (),
        properties: Sequence[str] = (),
        max_width: int = 10000,
        max_length: int | None = None,
    ):
        if self.trajectory is None:
            self._fail("No trajectory, try '?trajectory'", "trajectory")
            return

        if extra := set(properties) - VALID_PROPS.keys():
            self._fail(
                f"Invalid properties {extra}. Permitted properties: {', '.join(VALID_PROPS)}",
                "trajectory",
            )
            return

        properties = tuple(
            VALID_PROPS[prop] for prop in value_chain("index", "name", properties)
        )

        if not selection:
            selection = self.trajectory.atom_indices
        getter = itemgetter(*selection)

        info = {}
        for prop in properties:
            if prop in info:
                continue
            try:
                match prop:
                    case "charge":
                        info["charge"] = getter(self.trajectory.charges(frame))
                    case "fractional_coordinates":
                        info["fractional_coordinates"] = getter(
                            self.trajectory.coordinates(frame)
                        )
                    case "coordinates":
                        cc = cast(
                            FloatArray,
                            info["fractional_coordinates"]
                            if "fractional_coordinates" in info
                            else getter(self.trajectory.coordinates(frame)),
                        )
                        info["coordinates"] = self.trajectory.to_absolute_coordinates(
                            cc, frame, frame + 1, 1
                        )
                    case "species":
                        info["types"] = getter(self.trajectory.atom_types)
                    case "index":
                        info["index"] = getter(self.trajectory.atom_indices)
                    case "name":
                        info["name"] = getter(self.trajectory.atom_names)
                    case "cluster":
                        info["cluster"] = [
                            cluster
                            for _mol, cluster in getter(self.trajectory.cluster_indices)
                        ]
                    case "molecule":
                        info["molecule"] = [
                            mol
                            for mol, _cluster in getter(self.trajectory.cluster_indices)
                        ]
                    case "dummy":
                        info["dummy"] = [
                            str(bool(self.trajectory.get_atom_property(symb, "dummy")))
                            for symb in getter(self.trajectory.atom_types)
                        ]
            except Exception as err:
                self._info(f"Failed to load {prop} due to {err}")

        try:
            self._info(
                tabulate(
                    info,
                    PROP_TYPES,
                    header=self.ruler,
                    max_width=max_width,
                    max_length=max_length,
                )
            )
        except Exception as err:
            self._info(f"Cannot print table due to: {err}")

    def do_go(self, _args: str) -> bool:
        self._info("You have been eaten by a grue.")
        self._info("Game over.")
        return True

    def do_quit(self, args: str) -> bool:
        """Exit selection builder.

        Usage:
        quit
        """
        match parse(args):
            case []:
                return True
            case _:
                self._fail(f"Unknown args: {args!r}", "quit")
                return False

    do_EOF = do_quit

    def complete_results(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str] | tuple[str, ...]:
        ops = ("summary", "load", "clear", "print", "save", "plot")
        match parse(line.removeprefix("results")):
            case []:
                return ops
            case [word] if not line.endswith(" "):
                return self.fuzzy_complete(word, ops)
            case ["summary"] if not line.endswith(" "):
                return self.fuzzy_complete(word, ["verbose", *self.path_match(word)])
            case ["summary", word] if "verbose".startswith(word):
                return self.fuzzy_complete(word, ["verbose", *self.path_match(word)])
            case ["load"] if line.endswith(" "):
                return self.path_match("")
            case ["summary" | "load", pth] | ["summary", "verbose", pth]:
                return self.path_match(pth)
            case ["print"] if self.results is not None and line.endswith(" "):
                return list(map(str, self.results.all_children))
            case (
                ["print", ds] | ["print", "full", ds] | ["save", ds] | ["plot", ds]
            ) if self.results is not None:
                self._display(line, self.results_match(ds))
                return self.results_match(ds)
            case ["save", ds, pth] if self.results is not None and ds in self.results:
                return self.path_match(pth)
            case ["plot", ds, key] if self.results is not None and ds in self.results:
                return self.fuzzy_complete(
                    key, list(self.results[ds]._axes) + self.path_match(key)
                )
            case ["plot", ds, key, pth] if (
                self.results is not None and ds in self.results
            ):
                return self.path_match(pth)
            case ["save" | "print" | "plot", *_] if self.results is None:
                self._display(line, "No results, try '?results'")
                return []
            case _:
                self._display(line, "Unknown completion")
                return []

    def do_results(self, args: str):
        """Print information about a results file.

        Usage:
        results clear
        results load PATH
        results summary [verbose] [PATH]
        results print [full] [DATASET]
        results save DATASET [PATH]
        results plot DATASET [AXIS] [PATH]

        verbose prints full information about the `mda` file.
        """
        match parse(args):
            case []:
                self._fail("No arguments provided.", "results")
            case ["summary" | "print" | "save" | "plot", *_] if self.results is None:
                self._info("No results, try '?results'")
            case ["plot", *_] if not matplotlib_available:
                self._info("Matplotlib unavailable. Can't plot.")

            case ["clear"]:
                if self.results:
                    self.results.close()
                self.results = None
                self._update_prompt()
            case ["load", path]:
                try:
                    self.results = MDAFile(path)
                except ValueError as err:
                    self._info(err)
                    return
                self._update_prompt()
            case ["print" | "summary"] | ["print" | "summary", "verbose"]:
                self._info(self.results.summary(verbose="verbose" in args))
            case ["summary", path] | ["summary", "verbose", path]:
                self._info(MDAFile(path).summary(verbose="verbose" in args))

            case ["print", ds] | ["print", "full", ds]:
                try:
                    dataset = self.results[ds]
                except KeyError:
                    self._info(f"Key ({ds!r}) not in results.")
                    return

                header, data = dataset.as_table()

                self._info("\n".join(header) + "\n")

                data_o = data
                if args.split()[1] != "full":
                    data, data_o = (islice(x, 20) for x in islice(data, 10)), data

                self._info("\n".join(", ".join(str(x) for x in row) for row in data))

                if next(data_o, None) is not None:
                    self._info("\n...")

            case ["save", ds, out] if self.results is not None:
                with open(out, "w") as out_file:
                    header, data = self.results[ds].as_table()

                    out_file.writelines(map("{}\n".format, header))
                    writer = csv.writer(out_file)
                    writer.writerows(data)

            case ["plot", ds] if self.results is not None:
                self._plt(self.results, ds).show()

            case ["plot", ds, axis] if (
                self.results is not None and axis in self.results[ds]._axes
            ):
                self._plt(self.results, ds, axis).show()

            case ["plot", ds, axis, out] if (
                self.results is not None and axis in self.results[ds]._axes
            ):
                self._plt(self.results, ds, axis).savefig(out)

            case ["plot", ds, out] if self.results is not None:
                self._plt(self.results, ds).savefig(out)

            case _:
                self._fail(f"Unknown args: {args}.", "results")

    def _plt(self, file: MDAFile, name: str, axis: str | None = None) -> mpl.Figure:
        dataset = file[name]

        if axis is None:
            _, axis = dataset.longest_axis()

        dataset.set_data_limits(":", axis)

        fig, ax = mpl.subplots(1)
        fig.suptitle(str(dataset))

        for label, (x, y) in dataset.curves_vs_axis(axis, 9):
            ax.plot(x, y, label=label)
        ax.set_xlabel(f"{axis} ({dataset._axes_units[axis]})")
        fig.legend()

        return fig

    def do_element(self, args: str):
        """Get information about an element or elements.

        This reads from the loaded trajectory's database, falling back
        to the main ATOMS_DATABASE if none loaded.

        Usage:
        element list  -- Shows all elements in database.
        element search ELEMENTS...  -- Find all elements matching ELEMENTS...
        element ELEMENTS...  -- Print information on ELEMENTS...
        """
        match parse(args):
            case [] | ["search"]:
                self._fail("No elements requested.", "element")
            case ["list"]:
                execute_element(
                    Namespace(name=None, list=True, traj=self.trajectory, search=None)
                )
            case ["search", *elements]:
                for element in elements:
                    execute_element(
                        Namespace(
                            name=element, list=False, traj=self.trajectory, search=True
                        )
                    )
            case [*elements]:
                for element in elements:
                    execute_element(
                        Namespace(
                            name=element, list=False, traj=self.trajectory, search=None
                        )
                    )

    def _get_arg(self, name, conf: IConfigurator) -> str:
        type_str = type(conf).__name__.removesuffix("Configurator")
        type_str = " ".join(
            "".join(word) for word in split_before(type_str, str.isupper)
        )
        while True:
            inp = input(f"{name} [{type_str}] (default: {conf._default}) > ")
            if not inp:
                inp = conf._default
            try:
                conf.configure(inp)
                return inp
            except ConfigurationError:
                self._info(f"Invalid input {inp}")
                continue

    def _build_job(self, job: str, predef_args: list[str]) -> None:
        task = IJob.create(job)
        task.build_configuration()

        if predef_args:
            *inputs, output = predef_args
        else:
            inputs = []
            output = None

        parameters = {}
        for name, setting in task._configuration.items():
            match setting:
                case HDFTrajectoryConfigurator():
                    if self.trajectory:
                        inp = self.trajectory.filename
                        setting.configure(inp)
                    else:
                        inp = self._get_arg(name, setting)
                case MultiInputFileConfigurator():
                    if inputs:
                        inp = repr(inputs)
                        setting.configure(inp)
                    else:
                        inp = self._get_arg(name, setting)
                case FileWithAtomDataConfigurator():
                    if inputs:
                        inp = inputs.pop()
                        setting.configure(inp)
                    else:
                        inp = self._get_arg(name, setting)
                case OutputTrajectoryConfigurator() | OutputFilesConfigurator():
                    if output:
                        inp = output
                        setting.configure(inp)
                    else:
                        inp = self._get_arg(name, setting)

                case _:
                    inp = self._get_arg(name, setting)

            parameters[name] = inp

        task.run(parameters, status=True, prog_bar=True)

    def _run_job(self, job: str, args: list[str]):
        try:
            self._build_job(job, args)
        except KeyboardInterrupt:
            self._info("Cancelling...")

    def complete_converter(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str] | tuple[str, ...]:

        match parse(line.removeprefix("converter")):
            case []:
                return ["list", "save", "run", *CONVERTERS]
            case ["save" | "run"]:
                return CONVERTERS
            case ["save" | "run", conv] if conv in CONVERTERS:
                return self.path_match("")
            case ["save" | "run", word] if not line.endswith(" "):
                return self.fuzzy_complete(word, CONVERTERS)
            case ["save" | "run", conv, pth] if conv in CONVERTERS:
                return self.path_match(pth)
            case ["run", conv, *_, pth] if conv in CONVERTERS:
                return self.path_match(pth)
            case [word] if not line.endswith(" "):
                return self.fuzzy_complete(word, ["list", "save", *CONVERTERS])
            case _:
                self._info("\nUnknown completion")
                return []

    def do_converter(self, args: str):
        """Operations involving converter.

        Usage:
        converter list  -- List known converters.
        converter NAME  -- Print help for given converter.
        converter save NAME OUTPUT  -- Write a converter script to OUTPUT.
        converter run NAME INPUTS... OUTPUT     -- Run a converter with the given inputs.
        """
        match parse(args):
            case []:
                self._fail("No arguments provided", "converter")
            case ["list"]:
                execute_converter(Namespace(list=True, name=None, output=None))
            case [name] if name in CONVERTERS:
                execute_converter(Namespace(list=False, name=name, output=None))
            case ["save", name, output] if name in CONVERTERS:
                execute_converter(Namespace(list=False, name=name, output=output))
            case ["run", name, inp, *input, out] if name in CONVERTERS:
                self._run_job(name, [inp, *input, out])
                self.onecmd(f"trajectory load {out}")
            case ["run", name] if name in CONVERTERS:
                self._run_job(name, [])
            case _:
                self._fail(f"Unknown args: {args!r}", "converter")

    def complete_analysis(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str] | tuple[str, ...]:
        ops = ("list", "save", "run")

        match parse(line.removeprefix("analysis")):
            case []:
                return [*ops, *ANALYSES]
            case ["save" | "run"]:
                return ANALYSES
            case ["save" | "run", anal] if anal in ANALYSES:
                return self.path_match("")
            case ["save" | "run", word] if not line.endswith(" "):
                return self.fuzzy_complete(word, ANALYSES)
            case ["save" | "run", anal, pth] if anal in ANALYSES:
                return self.path_match(pth)
            case [word] if not line.endswith(" "):
                return self.fuzzy_complete(word, [*ops, *ANALYSES])
            case _:
                self._info("\nUnknown completion")
                return []

    def do_analysis(self, args: str):
        """Operations involving analysis.

        Usage:
        analysis list  -- List known analyses.
        analysis NAME  -- Print help for given analysis.
        analysis save NAME OUTPUT  -- Write a analysis script to OUTPUT.
        anylysis run NAME OUTPUT -- Run an analysis and write result to OUTPUT.

        Where NAME is the name of an :class:`IJob` instance.
        """
        match parse(args):
            case []:
                self._fail("No arguments provided", "analysis")
            case ["list"]:
                execute_analysis(
                    Namespace(list=True, name=None, output=None, traj=None)
                )
            case [name] if name in IJob.registry.raw_mapping.values():
                execute_analysis(
                    Namespace(list=False, name=name, output=None, traj=None)
                )
            case ["save", name, output] if name in IJob.registry.raw_mapping.values():
                execute_analysis(
                    Namespace(list=False, name=name, output=output, traj=None)
                )
            case ["run", name, output] if name in ANALYSES:
                self._run_job(name, [output])
                self.analysis = MDAFile(output)
                self._update_prompt()
            case ["run", name] if name in ANALYSES:
                self._run_job(name, [])
            case _:
                self._fail(f"Unknown args: {args!r}", "analysis")

    def complete_print(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        FIRST_WORDS = [
            "builder",
            "chemical_system",
            "trajectory_summary",
            "selection",
            "trajectory",
            "selection_full",
            "trajectory_full",
        ]

        match parse(line.removeprefix("print")):
            case []:
                return FIRST_WORDS
            case [word] if text:
                return self.fuzzy_complete(word, FIRST_WORDS)
            case ["chemical_system" | "trajectory_summary"]:
                return []
            case ["selection" | "trajectory" | "selection_full" | "trajectory_full"]:
                return ["frame", *PROP_TYPES]
            case [
                "selection" | "trajectory" | "selection_full" | "trajectory_full",
                "frame",
            ] if not text:
                return ["0"]
            case [
                "selection" | "trajectory" | "selection_full" | "trajectory_full",
                word,
            ] if text:
                return self.fuzzy_complete(word, ["frame", *sorted(PROPS)])
            case [
                "selection" | "trajectory" | "selection_full" | "trajectory_full",
                *present,
                word,
            ] if text:
                return self.fuzzy_complete(word, sorted(PROPS.difference(present)))
            case [
                "selection" | "trajectory" | "selection_full" | "trajectory_full",
                *present,
            ]:
                return sorted(PROPS.difference(present))
            case [
                "selection" | "trajectory" | "selection_full" | "trajectory_full",
                "frame",
                _,
                *present,
                word,
            ] if text:
                return self.fuzzy_complete(word, sorted(PROPS.difference(present)))
            case [
                "selection" | "trajectory" | "selection_full" | "trajectory_full",
                "frame",
                _,
                *present,
            ]:
                return sorted(PROPS.difference(present))
            case _:
                self._info("\nUnknown completion")
                return []

    def do_print(self, args: str):
        """Display info about current state.

        Usage:
        print builder   -- Print info about current selection builder
        print properties -- Print list of valid properties.
        print chemical_system  -- Print the chemical system of the currently loaded
                                  trajectory
        print trajectory_summary  -- Print a summary of the currently
                                     loaded trajectory
        print (selection | trajectory [full] [frame I] [PROPERTIES...]
              -- Print information about the current trajectory.
              - trajectory - Shows details about the whole trajectory.
              - selection - Shows only those atoms selected by the current builder.
              - frame I - Show details from the given frame (default = 0)
              - PROPERTIES - Show the given properties.

              By default this table is truncated to only show the first 20 matches,
              using the `full` variants shows the entire table.
        """
        match parse(args):
            case [] | ["builder"]:
                self._info(repr(self.builder))

            case ["properties"]:
                self._info(", ".join(PROP_TYPES))

            case ["chemical_system"]:
                self.onecmd("trajectory chemical_system")

            case ["trajectory_summary"]:
                self.onecmd("trajectory summary")

            case ["trajectory", "full", *properties]:
                self.onecmd("trajectory print full " + " ".join(properties))

            case ["selection", "full", *properties]:
                self.onecmd("select show full " + " ".join(properties))

            case ["selection" | "trajectory" as func, "frame", i, *properties] if (
                _list_type([i], int)
            ):
                select = "select" if func == "selection" else "trajectory"
                tmp_frame = self.frame
                self.onecmd(f"trajectory frame {i}")
                self.onecmd(f"{select} print " + " ".join(properties))
                self.onecmd(f"trajectory frame {tmp_frame}")

            case [
                "selection" | "trajectory" as func,
                "full",
                "frame",
                i,
                *properties,
            ] if _list_type([i], int):
                select = "select" if func == "selection" else "trajectory"
                tmp_frame = self.frame
                self.onecmd(f"trajectory frame {i}")
                self.onecmd(f"{select} print full " + " ".join(properties))
                self.onecmd(f"trajectory frame {tmp_frame}")

            case ["trajectory", *properties]:
                self.onecmd("trajectory print " + " ".join(properties))

            case ["selection", *properties]:
                self.onecmd("select show " + " ".join(properties))

            case _ if self.trajectory is None:
                self._info("No trajectory, try '?trajectory'")

            case _:
                self._fail(f"Unknown args: {args!r}", "print")

    def complete_trajectory(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        ops = [
            "load",
            "clear",
            "summary",
            "chemical_system",
            "frame",
            "print",
            "print_full",
        ]

        match parse(line.removeprefix("trajectory")):
            case []:
                return ops
            case ["clear", "summary", "chemical_system"]:
                return []
            case ["load"]:
                return self.path_match("")
            case ["load", pth]:
                return self.path_match(pth)
            case ["frame"] if not text:
                return ["0"]
            case ["print" | "print_full", word] if text:
                return self.fuzzy_complete(word, ["frame", *sorted(PROPS)])
            case ["print" | "print_full", *present, word] if text:
                return self.fuzzy_complete(word, sorted(PROPS.difference(present)))
            case ["print" | "print_full", *present]:
                return sorted(PROPS.difference(present))
            case [word] if text:
                return self.fuzzy_complete(word, ops)
            case _:
                self._info("\nUnknown completion")
                return []

    def do_trajectory(self, args: str):
        """Act on current trajectory.

        Usage:
        trajectory load PATH
        trajectory clear
        trajectory summary
        trajectory chemical_system
        trajectory frame I
        trajectory print [full] PROPERTIES...
        """
        match parse(args):
            case ["summary" | "chemical_system" | "frame" | "print", *_] if (
                self.trajectory is None
            ):
                self._info("No trajectory, try '?trajectory'")
            case ["load", path]:
                try:
                    self.trajectory = Trajectory(path)
                    self._info(f"Loaded trajectory {path}")
                    self.frame = 0
                except Exception as err:
                    self._info(f"Unable to load trajectory from {path} due to:\n {err}")
            case ["clear"]:
                self.trajectory = None
                self.frame = 0

            case ["summary"] if self.trajectory is not None:
                self._info(trajectory_summary(self.trajectory))

            case ["chemical_system"] if self.trajectory is not None:
                self._info(chemical_system_summary(self.trajectory.chemical_system))

            case ["frame", i] if self.trajectory is not None:
                frame = int(i)
                if not 0 <= frame < len(self.trajectory):
                    self._fail(
                        f"Frame outside trajectory (max: {len(self.trajectory) - 1})",
                        "trajectory",
                    )
                    return

                self.frame = frame

            case ["print", "full", *properties]:
                self.pprint_system(self.frame, selection=(), properties=properties)

            case ["print", *properties]:
                self.pprint_system(
                    self.frame,
                    selection=(),
                    properties=properties,
                    max_length=self.DEFAULT_TABLE,
                )

        self._update_prompt()

    def complete_select(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        ops = (
            "apply",
            "print",
            "show",
            "save",
            "load",
            "append",
            "delete",
            "reorder",
            "all",
            "none",
            "invert",
            "dummy",
            "types",
            "names",
            "labels",
            "list",
            "range",
            "slice",
            "molecules",
            "pattern",
            "sphere",
            "positions",
        )
        match parse(line.removeprefix("select")):
            case []:
                return list(ops)
            case ["load" | "append" | "save"]:
                return self.path_match("")
            case ["load" | "append" | "save", pth]:
                return self.path_match(pth)
            case ["delete" | "reorder", *args]:
                return [
                    str(i) for i, _ in enumerate(self.builder.ops) if str(i) not in args
                ]
            case [word] if text:
                return self.fuzzy_complete(word, ops)
            case _:
                return []

    def do_select(self, args: str):
        """Add new select criterion to current builder.

        Usage:
        select apply
        select print
        select show [full]
        select save PATH
        select load PATH
        select append PATH
        select delete I...
        select reorder I...
        select clear
        select all
        select none
        select invert
        select dummy [OP]
        select types [OP] TYPES...
        select names [OP] NAMES...
        select labels [OP] LABELS...
        select list [OP] I...
        select range [OP] START STOP
        select slice [OP] START STOP STEP
        select molecules [OP] MOLS...
        select pattern [OP] PATTERN
        select sphere [OP] [FRAME] X Y Z R
        select positions [OP] [FRAME] X0 Y0 Z0 X1 Y1 Z1

        OP is one of:
        =  SET
        &  INTERSECTION
        | + UNION  ADD
        -  DIFF DIFFERENCE

        With meanings as defined in :class:`SelectionBuilder`.
        """
        match parse(args):
            case []:
                self._fail("No arguments passed.", "select")
                return
            case [func, *vals]:
                fun: Callable[[list[str]], None] | None = getattr(
                    self, f"_select_{func}", None
                )
                if fun is None:
                    self._fail(f"Unknown func: {func}", "select")
                    return

                fun(vals)
                if func not in {"apply", "print", "show", "save"}:
                    self._info(self.builder)

    def _select_apply(self, args: list[str]):
        """Show which indices would be selected."""
        match args:
            case [] if self.trajectory is not None:
                self._info(
                    ", ".join(str(i) for i in self.builder.apply(self.trajectory))
                )
            case _ if self.trajectory is None:
                self._info("No trajectory, try '?trajectory'")
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_show(self, args: list[str]):
        """Show which indices would be selected."""
        match args:
            case ["full", *properties] if self.trajectory is not None:
                self.pprint_system(
                    self.frame,
                    selection=self.builder.apply(self.trajectory),
                    properties=properties,
                    max_length=None,
                )
            case [*properties] if self.trajectory is not None:
                self.pprint_system(
                    self.frame,
                    selection=self.builder.apply(self.trajectory),
                    properties=properties,
                    max_length=self.DEFAULT_TABLE,
                )

            case _ if self.trajectory is None:
                self._info("No trajectory, try '?trajectory'")

    def _select_print(self, args: list[str]):
        """Print selector."""
        match args:
            case []:
                self._info(repr(self.builder))
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_clear(self, args: list[str]):
        """Clear current selection."""
        match args:
            case []:
                self.builder.ops.clear()
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_save(self, args: list[str]):
        """Save current selection to file."""
        match args:
            case [out]:
                try:
                    pth = Path(out)
                    self.builder.save(pth)
                    self._info(f"Selection saved to {pth.absolute()}.")
                except Exception as err:
                    self._info(f"Failed to save selection to {out} due to:\n{err}")
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_load(self, args: list[str]) -> None:
        """Load a selection from path into the selection builder."""
        match args:
            case []:
                self._fail("No arguments provided", "select")
            case [path]:
                try:
                    self.builder = SelectionBuilder(path)
                except Exception as err:
                    self._info(f"Failed to load selection from {path} due to:\n{err}")
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_append(self, args: list[str]) -> None:
        """Append a selection from path into the selection builder."""
        match args:
            case []:
                self._fail("No arguments provided", "select")
            case [path]:
                try:
                    self.builder.load(path, append=True)
                except Exception as err:
                    self._info(f"Failed to load selection from {path} due to:\n{err}")

            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_delete(self, args: list[str]):
        match args:
            case []:
                self._fail("No arguments provided", "select")
            case [*args] if _list_type(args, int):
                rem = set(map(int, args))
                self.builder.reorder(
                    [i for i, _ in enumerate(self.builder.ops) if i not in rem]
                )

    def _select_reorder(self, args: list[str]):
        """Reorder selection operations."""
        match args:
            case []:
                self._fail("No arguments provided", "select")
            case [*order] if _list_type(order, int):
                self.builder.reorder([int(x) for x in order])

            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_sphere(self, args: list[str]):
        match args:
            case [op, frame, x, y, z, r] if (
                op in OPS_MAP
                and _list_type([frame], int)
                and _list_type([x, y, z, r], float)
            ):
                self.builder.select_sphere(
                    operation_type=OPS_MAP[op],
                    frame_number=int(frame),
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case [frame, x, y, z, r] if _list_type([frame], int) and _list_type(
                [x, y, z, r], float
            ):
                self.builder.select_sphere(
                    frame_number=int(frame),
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case [op, x, y, z, r] if op in OPS_MAP and _list_type([x, y, z, r], float):
                self.builder.select_sphere(
                    operation_type=OPS_MAP[op],
                    frame_number=self.frame,
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case [x, y, z, r] if _list_type([x, y, z, r], float):
                self.builder.select_sphere(
                    frame_number=self.frame,
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_positions(self, args: list[str]):
        """Select by cuboid."""
        match args:
            case [op, frame, x0, y0, z0, x1, y1, z1] if (
                op in OPS_MAP
                and _list_type([frame], int)
                and _list_type([x0, y0, z0, x1, y1, z1], float)
            ):
                self.builder.select_positions(
                    operation_type=OPS_MAP[op],
                    frame_number=int(frame),
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case [op, x0, y0, z0, x1, y1, z1] if op in OPS_MAP and _list_type(
                [x0, y0, z0, x1, y1, z1], float
            ):
                self.builder.select_positions(
                    operation_type=OPS_MAP[op],
                    frame_number=self.frame,
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case [frame, x0, y0, z0, x1, y1, z1] if _list_type(
                [frame], int
            ) and _list_type([x0, y0, z0, x1, y1, z1], float):
                self.builder.select_positions(
                    frame_number=int(frame),
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case [x0, y0, z0, x1, y1, z1] if _list_type(
                [x0, y0, z0, x1, y1, z1], float
            ):
                self.builder.select_positions(
                    operation_type=OPS_MAP[op],
                    frame_number=int(frame),
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_pattern(self, args: list[str]):
        """Select by rdkit pattern."""
        match args:
            case [op, pattern] if op in OPS_MAP:
                self.builder.select_pattern(
                    operation_type=OPS_MAP[op], rdkit_pattern=pattern
                )

            case [pattern]:
                self.builder.select_pattern(rdkit_pattern=pattern)
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_labels(self, args: list[str]):
        """Select by atom labels (including residues)."""
        match args:
            case []:
                self._fail("No arguments provided", "select")

            case [op, *labels] if op in OPS_MAP:
                self.builder.select_labels(
                    operation_type=OPS_MAP[op], atom_labels=labels
                )

            case [*labels]:
                self.builder.select_labels(atom_labels=labels)

    def _select_molecules(self, args: list[str]):
        """Select molecules by name."""
        match args:
            case []:
                self._fail("No molecules specified.", "select")

            case [op] if op in OPS_MAP:
                self._fail("No molecules specified.", "select")

            case [op, *mols] if op in OPS_MAP:
                self.builder.select_molecules(
                    operation_type=OPS_MAP[op], molecule_names=mols
                )

            case [*mols]:
                self.builder.select_molecules(molecule_names=mols)

    def _select_dummy(self, args: list[str]):
        """Select dummy atoms."""
        match args:
            case []:
                self.builder.select_dummy()
                return

            case [op] if op in OPS_MAP:
                self.builder.select_dummy(operation_type=OPS_MAP[op])
                return

        self._fail(f"Unknown args: {args!r}", "select")

    def _select_invert(self, args: list[str]):
        """Invert selection."""
        match args:
            case []:
                self.builder.invert_selection()
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_none(self, args: list[str]):
        """Select nothing."""
        match args:
            case []:
                self.builder.select_none()
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_all(self, args: list[str]):
        """Select all."""
        match args:
            case []:
                self.builder.select_all()
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_list(self, args: list[str]):
        """Select by atom indices."""
        match args:
            case [op, *args] if op in OPS_MAP and args and _list_type(args, int):
                self.builder.select_atoms(
                    operation_type=OPS_MAP[op], index_list=[*map(int, args)]
                )
            case [*args] if args and _list_type(args, int):
                self.builder.select_atoms(index_list=[*map(int, args)])
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_range(self, args: list[str]):
        """Select by 2-element (start, stop) slice."""
        match args:
            case [op, a, b] if op in OPS_MAP and _list_type([a, b], int):
                self.builder.select_atoms(
                    operation_type=OPS_MAP[op], index_range=[int(a), int(b)]
                )
            case [a, b] if _list_type([a, b], int):
                self.builder.select_atoms(index_range=[int(a), int(b)])
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_slice(self, args: list[str]):
        """Select by 3-element (start, stop, step) slice."""
        match args:
            case [op, a, b, c] if op in OPS_MAP and _list_type([a, b, c], int):
                self.builder.select_atoms(
                    operation_type=OPS_MAP[op], index_slice=[int(a), int(b), int(c)]
                )

            case [a, b, c] if _list_type([a, b, c], int):
                self.builder.select_atoms(index_slice=[int(a), int(b), int(c)])
            case _:
                self._fail(f"Unknown args: {args!r}", "select")

    def _select_types(self, args: list[str]):
        """Select by atom types."""
        match args:
            case []:
                self._fail("No arguments provided", "select")

            case [op, *types] if op in OPS_MAP:
                self.builder.select_atoms(operation_type=OPS_MAP[op], atom_types=types)
            case [*types]:
                self.builder.select_atoms(atom_types=types)

    def _select_names(self, args: list[str]):
        """Select by atom names."""
        match args:
            case []:
                self._fail("No arguments provided", "select")

            case [op, *names] if op in OPS_MAP:
                self.builder.select_atoms(operation_type=OPS_MAP[op], atom_names=names)
            case [*names]:
                self.builder.select_atoms(atom_names=names)


def main() -> None:
    MDANSETui().cmdloop()


if __name__ == "__main__":
    main()
