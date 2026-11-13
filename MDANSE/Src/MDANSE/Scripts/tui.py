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

# ruff: file-ignore[PLR0911]
from __future__ import annotations

import cmd
from argparse import Namespace
from collections.abc import Callable, Iterable, Sequence
from difflib import get_close_matches
from operator import itemgetter
from pathlib import Path

from MDANSE.Framework.AtomSelector.selection_builder import (
    OperationType,
    SelectionBuilder,
)
from MDANSE.Framework.Converters import Converter
from MDANSE.Framework.Jobs import IJob
from MDANSE.IO.IOUtils import tabulate
from MDANSE.MolecularDynamics.Trajectory import (
    Trajectory,
    chemical_system_summary,
    trajectory_summary,
)
from MDANSE.Scripts.funcs import (
    execute_analysis,
    execute_converter,
    execute_element,
    execute_results,
)

OPS_MAP = {
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

VALID_PROPS = {
    alias: prop
    for prop, aliases in {
        "charge": ("charge", "q"),
        "fractional_coordinates": (
            "fractional_coordinates",
            "frac",
            "fractional",
            "frac_coords",
        ),
        "coordinates": ("coordinates", "abs", "absolute", "pos", "position", "coords"),
        "types": ("types", "species", "spec"),
        "index": ("index", "indices", "ind"),
        "name": ("name", "names", "label", "labels"),
        "cluster": ("cluster", "groups"),
        "molecule": ("molecule", "mol"),
        "dummy": ("dummy",),
    }.items()
    for alias in aliases
}
PROP_TYPES = {
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


def parse(line: str) -> list[str]:
    return line.split()


def list_type(in_list: list[str], typ: type) -> bool:
    try:
        [typ(x) for x in in_list]
    except Exception:
        return False
    else:
        return True


class MDANSETui(cmd.Cmd):
    intro = "Welcome to the MDANSE TUI. Type help or ? to list commands.\n"
    prompt = "mdanse > "
    identchars = cmd.IDENTCHARS + "/"

    def info(self, *args, **kwargs):
        print(*args, **kwargs, file=self.stdout)

    def fail(self, cause: str, caller: str = ""):
        self.info(cause)
        if caller:
            self.info()
            self.do_help(caller)

    def cmdloop(self, *_):
        super().cmdloop()

    @staticmethod
    def fuzzy_complete(curr: str, words: Iterable[str]) -> list[str]:
        if w := [word for word in words if word.startswith(curr)]:
            return w
        return get_close_matches(curr, words, cutoff=0.1)

    @staticmethod
    def path_match(text: str) -> list[str]:
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
        **kwargs,
    ):
        if self.trajectory is None:
            self.fail("No trajectory, try '?load'", "print")
            return

        if extra := set(properties) - VALID_PROPS.keys():
            self.fail(
                f"Invalid properties {extra}. Permitted properties: {', '.join(VALID_PROPS)}",
                "print",
            )
            return

        if not properties:
            properties = ("index", "name")

        properties = tuple(VALID_PROPS[prop] for prop in properties)

        if not selection:
            selection = self.trajectory.atom_indices
        getter = itemgetter(*selection)

        info = {}
        for prop in properties:
            if prop in info:
                continue
            match prop:
                case "charge":
                    info["charge"] = getter(self.trajectory.charges(frame))
                case "fractional_coordinates":
                    info["fractional_coordinates"] = getter(
                        self.trajectory.coordinates(frame)
                    )
                case "coordinates":
                    cc = (
                        info["fractional_coordinates"]
                        if "fractional_coordinates" in info
                        else getter(self.trajectory.coordinates(frame))
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
                        mol for mol, _cluster in getter(self.trajectory.cluster_indices)
                    ]
                case "dummy":
                    info["dummy"] = [
                        str(bool(self.trajectory.get_atom_property(symb, "dummy")))
                        for symb in getter(self.trajectory.atom_types)
                    ]

        self.info(tabulate(info, PROP_TYPES, header=self.ruler, **kwargs))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.builder = SelectionBuilder()
        self.trajectory = None

    def emptyline(self): ...

    def do_go(self, args: str) -> bool:
        self.info("You have been eaten by a grue.")
        self.info("Game over")
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
                self.fail(f"Unknown args: {args!r}", "quit")
                return False

    do_EOF = do_quit

    def complete_results(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        match parse(line.removeprefix("results")):
            case []:
                return ["verbose", *self.path_match("")]
            case [word] if "verbose".startswith(word):
                return self.fuzzy_complete(word, ["verbose", *self.path_match(word)])
            case [pth] | ["verbose", pth]:
                return self.path_match(pth)
            case _:
                self.info("\nUnknown completion")
                return []

    def do_results(self, args: str):
        """Print information about a results file.

        Usage:
        results [verbose] PATH

        verbose prints full information about the `mda` file.
        """
        match parse(args):
            case []:
                self.fail("No arguments provided.", "results")
            case [path]:
                execute_results(Namespace(file_name=path, verbose=False))
            case ["verbose", path]:
                execute_results(Namespace(file_name=path, verbose=True))
            case _:
                self.fail(f"Unknown args: {args}.", "results")

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
                self.fail("No elements requested.", "element")
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

    def complete_converter(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        conv = list(Converter.registry.raw_mapping)

        match parse(line.removeprefix("converter")):
            case []:
                return ["list", "save", *conv]
            case ["save"]:
                return conv
            case ["save", c] if c in conv:
                return self.path_match("")
            case ["save", word] if not line.endswith(" "):
                return self.fuzzy_complete(word, conv)
            case ["save", c, pth] if c in conv:
                return self.path_match(pth)
            case [word] if not line.endswith(" "):
                return self.fuzzy_complete(word, ["list", "save", *conv])
            case _:
                self.info("\nUnknown completion")
                return []

    def do_converter(self, args: str):
        """Operations involving converter.

        Usage:
        converter list  -- List known converters.
        converter NAME  -- Print help for given converter.
        converter save NAME OUTPUT  -- Write a converter script to OUTPUT.
        """
        match parse(args):
            case []:
                self.fail("No arguments provided", "converter")
            case ["list"]:
                execute_converter(Namespace(list=True, name=None, output=None))
            case [name]:
                execute_converter(Namespace(list=False, name=name, output=None))
            case ["save", name, output]:
                execute_converter(Namespace(list=False, name=name, output=output))
            case _:
                self.fail(f"Unknown args: {args!r}", "converter")

    def complete_analysis(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        conv = list(IJob.registry.raw_mapping.values())

        match parse(line.removeprefix("analysis")):
            case []:
                return ["list", "save", *conv]
            case ["save"]:
                return conv
            case ["save", c] if c in conv:
                return self.path_match("")
            case ["save", word] if not line.endswith(" "):
                return self.fuzzy_complete(word, conv)
            case ["save", c, pth] if c in conv:
                return self.path_match(pth)
            case [word] if not line.endswith(" "):
                return self.fuzzy_complete(word, ["list", "save", *conv])
            case _:
                self.info("\nUnknown completion")
                return []

    def do_analysis(self, args: str):
        """Operations involving analysis.

        Usage:
        analysis list  -- List known analyses.
        analysis NAME  -- Print help for given analysis.
        analysis save NAME OUTPUT  -- Write a analysis script to OUTPUT.

        Where NAME is the name of an :class:`IJob` instance.
        """
        match parse(args):
            case []:
                self.fail("No arguments provided", "analysis")
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
            case _:
                self.fail(f"Unknown args: {args!r}", "analysis")

    def complete_print(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        FIRST_WORDS = [
            "builder",
            "chemical_system",
            "trajectory_summary",
            "selection",
            "system",
            "selection_full",
            "system_full",
        ]

        props = set(VALID_PROPS)

        match parse(line.removeprefix("print")):
            case []:
                return FIRST_WORDS
            case [word] if text:
                return self.fuzzy_complete(word, FIRST_WORDS)
            case ["chemical_system" | "trajectory_summary"]:
                return []
            case ["selection" | "system" | "selection_full" | "system_full"]:
                return ["frame", *PROP_TYPES]
            case [
                "selection" | "system" | "selection_full" | "system_full",
                "frame",
            ] if not text:
                return ["0"]
            case ["selection" | "system" | "selection_full" | "system_full", word] if (
                text
            ):
                return self.fuzzy_complete(word, ["frame", *sorted(props)])
            case [
                "selection" | "system" | "selection_full" | "system_full",
                *present,
                word,
            ] if text:
                return self.fuzzy_complete(word, sorted(props.difference(present)))
            case ["selection" | "system" | "selection_full" | "system_full", *present]:
                return sorted(props.difference(present))
            case [
                "selection" | "system" | "selection_full" | "system_full",
                "frame",
                _,
                *present,
                word,
            ] if text:
                return self.fuzzy_complete(word, sorted(props.difference(present)))
            case [
                "selection" | "system" | "selection_full" | "system_full",
                "frame",
                _,
                *present,
            ]:
                return sorted(props.difference(present))
            case _:
                self.info("\nUnknown completion")
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
        print (selection[_full] | system[_full]) [frame I] [PROPERTIES...]
              -- Print information about the current system.
              - system - Shows details about the whole system.
              - selection - Shows only those atoms selected by the current builder.
              - frame I - Show details from the given frame (default = 0)
              - PROPERTIES - Show the given properties.

              By default this table is truncated to only show the first 20 matches,
              using the `_full` variants shows the entire table.
        """

        words = parse(args)

        if not words:
            self.info(repr(self.builder))
            return

        select = words[0] in ("selection", "selection_full")
        frame = 0
        limit = None if words[0].endswith("_full") else 20

        match words:
            case ["properties"]:
                self.info(", ".join(PROP_TYPES))
                return
            case ["builder"]:
                self.info(repr(self.builder))
                return
            case ["chemical_system"] if (
                self.trajectory is not None  # Falls through to check
            ):
                self.info(chemical_system_summary(self.trajectory.chemical_system))
                return
            case ["trajectory_summary"] if (
                self.trajectory is not None  # Falls through to check
            ):
                self.info(trajectory_summary(self.trajectory))
                return

            case [
                "selection" | "selection_full" | "system" | "system_full",
                "frame",
                i,
                *properties,
            ] if list_type([i], int) and self.trajectory is not None:
                frame = int(i)
                disp = properties

            case [
                "selection" | "selection_full" | "system" | "system_full",
                *properties,
            ] if self.trajectory is not None:
                disp = properties

            case _ if self.trajectory is None:
                self.info("No trajectory, try '?load'")
                return
            case _:
                self.fail(f"Unknown args: {args!r}", "print")
                return

        selection = self.builder.apply(self.trajectory) if select else set[int]()

        self.pprint_system(
            frame, selection=selection, properties=disp, max_length=limit
        )

    def complete_load(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        match parse(line.removeprefix("load")):
            case []:
                return ["selection", "system"]
            case [word] if text:
                return self.fuzzy_complete(word, ["selection", "system"])
            case ["selection" | "system"]:
                return self.path_match("")
            case ["selection" | "system", pth]:
                return self.path_match(pth)
            case _:
                self.info("\nUnknown completion")
                return []

    def do_load(self, args: str):
        """Load data from path.

        Usage:
        load system PATH  -- Load an `mdt` from PATH as current system.
        load selection PATH  -- Load a json file from PATH as current builder.
        """
        match parse(args):
            case ["system", path]:
                try:
                    self.trajectory = Trajectory(path)
                    self.info(f"Loaded trajectory {path}")
                    self.prompt = f"mdanse Traj:{Path(path).name} > "
                except Exception as err:
                    self.info(f"Unable to load trajectory from {path} due to:\n {err}")

            case ["selection", path]:
                self._select_load([path])

            case _:
                self.fail(f"Unknown args: {args!r}", "load")

    def complete_select(
        self, text: str, line: str, _begidx: str, _endidx: str
    ) -> list[str]:
        ops = (
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
                self.fail("No arguments passed.", "select")
                return
            case [func, *vals]:
                fun: Callable[[list[str]], None] | None = getattr(
                    self, f"_select_{func}", None
                )
                if fun is None:
                    self.fail(f"Unknown func: {func}", "select")
                    return

                fun(vals)
                self.info(self.builder)

    def _select_clear(self, args: list[str]):
        """Clear current selection."""
        match args:
            case []:
                self.builder.ops.clear()
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_save(self, args: list[str]):
        """Save current selection to file."""
        match args:
            case [out]:
                try:
                    pth = Path(out)
                    self.builder.save(pth)
                    self.info(f"Selection saved to {pth.absolute()}.")
                except Exception as err:
                    self.info(f"Failed to save selection to {out} due to:\n{err}")
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_load(self, args: list[str]) -> None:
        """Load a selection from path into the selection builder."""
        match args:
            case []:
                self.fail("No arguments provided", "select")
            case [path]:
                try:
                    self.builder = SelectionBuilder(path)
                except Exception as err:
                    self.info(f"Failed to load selection from {path} due to:\n{err}")
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_append(self, args: list[str]) -> None:
        """Append a selection from path into the selection builder."""
        match args:
            case []:
                self.fail("No arguments provided", "select")
            case [path]:
                try:
                    self.builder.load(path, append=True)
                except Exception as err:
                    self.info(f"Failed to load selection from {path} due to:\n{err}")

            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_delete(self, args: list[str]):
        match args:
            case []:
                self.fail("No arguments provided", "select")
            case [*args] if list_type(args, int):
                rem = set(map(int, args))
                self.builder.reorder(
                    [i for i, _ in enumerate(self.builder.ops) if i not in rem]
                )

    def _select_reorder(self, args: list[str]):
        """Reorder selection operations."""
        match args:
            case []:
                self.fail("No arguments provided", "select")
            case [*order] if list_type(order, int):
                self.builder.reorder([int(x) for x in order])

            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_sphere(self, args: list[str]):
        match args:
            case [op, frame, x, y, z, r] if (
                op in OPS_MAP
                and list_type([frame], int)
                and list_type([x, y, z, r], float)
            ):
                self.builder.select_sphere(
                    operation_type=OPS_MAP[op],
                    frame_number=int(frame),
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case [frame, x, y, z, r] if list_type([frame], int) and list_type(
                [x, y, z, r], float
            ):
                self.builder.select_sphere(
                    frame_number=int(frame),
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case [op, x, y, z, r] if op in OPS_MAP and list_type([x, y, z, r], float):
                self.builder.select_sphere(
                    operation_type=OPS_MAP[op],
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case [x, y, z, r] if list_type([x, y, z, r], float):
                self.builder.select_sphere(
                    sphere_centre=(float(x), float(y), float(z)),
                    sphere_radius=float(r),
                )

            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_positions(self, args: list[str]):
        """Select by cuboid."""
        match args:
            case [op, frame, x0, y0, z0, x1, y1, z1] if (
                op in OPS_MAP
                and list_type([frame], int)
                and list_type([x0, y0, z0, x1, y1, z1], float)
            ):
                self.builder.select_positions(
                    operation_type=OPS_MAP[op],
                    frame_number=int(frame),
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case [op, x0, y0, z0, x1, y1, z1] if op in OPS_MAP and list_type(
                [x0, y0, z0, x1, y1, z1], float
            ):
                self.builder.select_positions(
                    operation_type=OPS_MAP[op],
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case [frame, x0, y0, z0, x1, y1, z1] if list_type(
                [frame], int
            ) and list_type([x0, y0, z0, x1, y1, z1], float):
                self.builder.select_positions(
                    frame_number=int(frame),
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case [x0, y0, z0, x1, y1, z1] if list_type([x0, y0, z0, x1, y1, z1], float):
                self.builder.select_positions(
                    operation_type=OPS_MAP[op],
                    frame_number=int(frame),
                    position_minimum=(float(x0), float(y0), float(z0)),
                    position_maximum=(float(x1), float(y1), float(z1)),
                )
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

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
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_labels(self, args: list[str]):
        """Select by atom labels (including residues)."""
        match args:
            case []:
                self.fail("No arguments provided", "select")

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
                self.fail("No molecules specified.", "select")

            case [op] if op in OPS_MAP:
                self.fail("No molecules specified.", "select")

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

        self.fail(f"Unknown args: {args!r}", "select")

    def _select_invert(self, args: list[str]):
        """Invert selection."""
        match args:
            case []:
                self.builder.invert_selection()
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_none(self, args: list[str]):
        """Select nothing."""
        match args:
            case []:
                self.builder.select_none()
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_all(self, args: list[str]):
        """Select all."""
        match args:
            case []:
                self.builder.select_all()
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_list(self, args: list[str]):
        """Select by atom indices."""
        match args:
            case [op, *args] if op in OPS_MAP and args and list_type(args, int):
                self.builder.select_atoms(
                    operation_type=OPS_MAP[op], index_list=[*map(int, args)]
                )
            case [*args] if args and list_type(args, int):
                self.builder.select_atoms(index_list=[*map(int, args)])
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_range(self, args: list[str]):
        """Select by 2-element (start, stop) slice."""
        match args:
            case [op, a, b] if op in OPS_MAP and list_type([a, b], int):
                self.builder.select_atoms(
                    operation_type=OPS_MAP[op], index_range=[int(a), int(b)]
                )
            case [a, b] if list_type([a, b], int):
                self.builder.select_atoms(index_range=[int(a), int(b)])
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_slice(self, args: list[str]):
        """Select by 3-element (start, stop, step) slice."""
        match args:
            case [op, a, b, c] if op in OPS_MAP and list_type([a, b, c], int):
                self.builder.select_atoms(
                    operation_type=OPS_MAP[op], index_slice=[int(a), int(b), int(c)]
                )

            case [a, b, c] if list_type([a, b, c], int):
                self.builder.select_atoms(index_list=[int(a), int(b), int(c)])
            case _:
                self.fail(f"Unknown args: {args!r}", "select")

    def _select_types(self, args: list[str]):
        """Select by atom types."""
        match args:
            case []:
                self.fail("No arguments provided", "select")

            case [op, *types] if op in OPS_MAP:
                self.builder.select_atoms(operation_type=OPS_MAP[op], atom_types=types)
            case [*types]:
                self.builder.select_atoms(atom_types=types)

    def _select_names(self, args: list[str]):
        """Select by atom names."""
        match args:
            case []:
                self.fail("No arguments provided", "select")

            case [op, *names] if op in OPS_MAP:
                self.builder.select_atoms(operation_type=OPS_MAP[op], atom_names=names)
            case [*names]:
                self.builder.select_atoms(atom_names=names)


def main() -> None:
    MDANSETui().cmdloop()


if __name__ == "__main__":
    main()
