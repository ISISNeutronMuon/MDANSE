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

import re
from collections import namedtuple
from collections.abc import Iterable, Sequence
from itertools import starmap
from pathlib import Path
from string import ascii_uppercase as upcase
from typing import Any, Literal

import numpy as np
from more_itertools import first, first_true, split_before, spy
from numpy.typing import NDArray

from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Converters.LAMMPS import BoxStyle
from MDANSE.IO.IOUtils import strip_comments
from MDANSE.MLogging import LOG

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class LAMMPSConfigFileError(Error):
    pass


SECTION_HEADERS = (
    "Atoms",
    "Velocities",
    "Masses",
    "Ellipsoids",
    "Lines",
    "Triangles",
    "Bodies",
    "Bonds",
    "Angles",
    "Dihedrals",
    "Impropers",
    "Atom Type Labels",
    "Bond Type Labels",
    "Angle Type Labels",
    "Dihedral Type Labels",
    "Improper Type Labels",
    "Pair Coeffs",
    "PairIJ Coeffs",
    "Bond Coeffs",
    "Angle Coeffs",
    "Dihedral Coeffs",
    "Improper Coeffs",
    "BondBond Coeffs",
    "BondAngle Coeffs",
    "MiddleBondTorsion Coeffs",
    "EndBondTorsion Coeffs",
    "AngleTorsion Coeffs",
    "AngleAngleTorsion Coeffs",
    "BondBond13 Coeffs",
    "AngleAngle Coeffs",
)

ATOM_TYPES_MAP = {
    "atomic": ("atom_ID", "atom_type", "x", "y", "z"),
    "charge": ("atom_ID", "atom_type", "q", "x", "y", "z"),
    "bond": ("atom_ID", "molecule_ID", "atom_type", "x", "y", "z"),
    "angle": ("atom_ID", "molecule_ID", "atom_type", "x", "y", "z"),
    "full": ("atom_ID", "molecule_ID", "atom_type", "q", "x", "y", "z"),
    "body": ("atom_ID", "atom_type", "bodyflag", "mass", "x", "y", "z"),
    "molecular": ("atom_ID", "molecule_ID", "atom_type", "x", "y", "z"),
    # Prioritise basic types.
    "atomic_w_image": ("atom_ID", "atom_type", "x", "y", "z", "ix", "iy", "iz"),
    "charge_w_image": ("atom_ID", "atom_type", "q", "x", "y", "z", "ix", "iy", "iz"),
    "bond_w_image": (
        "atom_ID",
        "molecule_ID",
        "atom_type",
        "x",
        "y",
        "z",
        "ix",
        "iy",
        "iz",
    ),
    "angle_w_image": (
        "atom_ID",
        "molecule_ID",
        "atom_type",
        "x",
        "y",
        "z",
        "ix",
        "iy",
        "iz",
    ),
    "full_w_image": (
        "atom_ID",
        "molecule_ID",
        "atom_type",
        "q",
        "x",
        "y",
        "z",
        "ix",
        "iy",
        "iz",
    ),
    "body_w_image": (
        "atom_ID",
        "atom_type",
        "bodyflag",
        "mass",
        "x",
        "y",
        "z",
        "ix",
        "iy",
        "iz",
    ),
    "molecular_w_image": (
        "atom_ID",
        "molecule_ID",
        "atom_type",
        "x",
        "y",
        "z",
        "ix",
        "iy",
        "iz",
    ),
    "bpm/sphere": (
        "atom_ID",
        "molecule_ID",
        "atom_type",
        "diameter",
        "density",
        "x",
        "y",
        "z",
    ),
    "dielectric": (
        "atom_ID",
        "atom_type",
        "q",
        "x",
        "y",
        "z",
        "mux",
        "muy",
        "muz",
        "area",
        "ed",
        "em",
        "epsilon",
        "curvature",
    ),
    "dipole": ("atom_ID", "atom_type", "q", "x", "y", "z", "mux", "muy", "muz"),
    "dpd": ("atom_ID", "atom_type", "theta", "x", "y", "z"),
    "edpd": ("atom_ID", "atom_type", "edpd_temp", "edpd_cv", "x", "y", "z"),
    "electron": ("atom_ID", "atom_type", "q", "espin", "eradius", "x", "y", "z"),
    "ellipsoid": ("atom_ID", "atom_type", "ellipsoidflag", "density", "x", "y", "z"),
    "line": (
        "atom_ID",
        "molecule_ID",
        "atom_type",
        "lineflag",
        "density",
        "x",
        "y",
        "z",
    ),
    "mdpd": ("atom_ID", "atom_type", "rho", "x", "y", "z"),
    "peri": ("atom_ID", "atom_type", "volume", "density", "x", "y", "z"),
    "rheo": ("atom_ID", "atom_type", "status", "rho", "x", "y", "z"),
    "rheo/thermal": ("atom_ID", "atom_type", "status", "rho", "energy", "x", "y", "z"),
    "smd": (
        "atom_ID",
        "atom_type",
        "molecule",
        "volume",
        "mass",
        "kradius",
        "cradius",
        "x0",
        "y0",
        "z0",
        "x",
        "y",
        "z",
    ),
    "sph": ("atom_ID", "atom_type", "rho", "esph", "cv", "x", "y", "z"),
    "sphere": ("atom_ID", "atom_type", "diameter", "density", "x", "y", "z"),
    "spin": ("atom_ID", "atom_type", "x", "y", "z", "spx", "spy", "spz", "sp"),
    "template": (
        "atom_ID",
        "atom_type",
        "molecule_ID",
        "template_index",
        "template_atom",
        "x",
        "y",
        "z",
    ),
    "tri": (
        "atom_ID",
        "molecule_ID",
        "atom_type",
        "triangleflag",
        "density",
        "x",
        "y",
        "z",
    ),
    "wavepacket": (
        "atom_ID",
        "atom_type",
        "q",
        "espin",
        "eradius",
        "etag",
        "cs_re",
        "cs_im",
        "x",
        "y",
        "z",
    ),
    "tdpd": ("atom_ID", "atom_type", "x", "y", "z", "cc1", "cc2", ..., "ccNspecies"),
    "hybrid": ("atom_ID", "atom_type", "x", "y", "z", "sub_style1", "sub_style2", ...),
}

ATOM_TYPES_MAP.update(
    {
        f"{key}_w_image": value + ("ix", "iy", "iz")
        for key, value in ATOM_TYPES_MAP.items()
    }
)


KEY_TYPES_MAP = {
    r"(atom|molecule)_ID": int,
    r"atom_type": int,
    r"i[xyz]": int,
    r"[a-z]+flag": bool,
    r"e(spin|tag)": int,
    r"template_[a-z]+": int,
    r"status": int,
    r".*": float,
}

AtomTypes = Literal[
    "angle",
    "atomic",
    "body",
    "bond",
    "bpm/sphere",
    "charge",
    "dielectric",
    "dipole",
    "dpd",
    "edpd",
    "electron",
    "ellipsoid",
    "full",
    "line",
    "mdpd",
    "molecular",
    "peri",
    "rheo",
    "rheo/thermal",
    "smd",
    "sph",
    "sphere",
    "spin",
    "tdpd",
    "template",
    "tri",
    "wavepacket",
    "hybrid",
]

DESIRED = {"header", "Masses", "Atom Type Labels", "Bonds", "Atoms"}

# Regexps to recognise numbers
FNUMBER_RE = r"(?:[+-]?(?:\d*\.\d+|\d+\.\d*))"
INTNUMBER_RE = r"(?:[+-]?(?<!\.)\d+(?!\.))"
EXPNUMBER_RE = rf"(?:(?:{FNUMBER_RE}|{INTNUMBER_RE})[Ee][+-]?\d{{1,3}})"
EXPFNUMBER_RE = f"(?:{EXPNUMBER_RE}|{FNUMBER_RE})"


def one_to_one_parser(lines, *_) -> dict[str, str]:
    return dict(map(str.split, strip_comments(lines)))


def float_list_parser(lines, *_) -> dict[str, tuple[float, ...]]:
    return {
        line.split()[0]: tuple(map(float, line.split()[1:]))
        for line in strip_comments(lines)
        if line
    }


def int_list_parser(lines, *_) -> dict[str, tuple[int, ...]]:
    return {
        line.split()[0]: tuple(map(int, line.split()[1:]))
        for line in strip_comments(lines)
        if line
    }


class ConfigFileConfigurator(FileWithAtomDataConfigurator):
    """Parse the result of a LAMMPS ``write_data``.

    Provides necessary initial details if not included in
    trajectory.
    """

    @staticmethod
    def header_parser(lines: Iterable[str]) -> dict[str, Any]:
        """Parse config header.

        Parameters
        ----------
        lines : Iterable[str]
            Block containing header information.

        Returns
        -------
        Dict[str, Any]
            Information contained in header.

        Raises
        ------
        LAMMPSConfigFileError
            If header doesn't have cell.

        Notes
        -----
        All parsed atom indices are shifted with respect to lammps.
        Lammps is 1-indexed, the values here are 0-indexed.
        """
        header = {
            match[2].strip(): match[1]
            for line in lines
            if (match := re.search("(.*?)([a-z ]+)$", line))
        }

        accum = {
            f"n_{key.replace(' ', '_')}": int(header.get(key, 0))
            for key in (
                "atoms",
                "bonds",
                "angles",
                "dihedrals",
                "impropers",
                "atom types",
                "bond types",
                "angle types",
                "dihedral types",
                "improper types",
            )
        }
        if "xy xz yz" in header:
            cell = np.empty((3, 3), dtype=float)
            cell[:, :2] = [
                header[row].split() for row in ("xlo xhi", "ylo yhi", "zlo zhi")
            ]
            cell[:, 2] = header["xy xz yz"].split()
            accum["style"] = BoxStyle.NONORTHOGONAL
        elif "zlo zhi" in header:
            cell = np.array(
                [header[row].split() for row in ("xlo xhi", "ylo yhi", "zlo zhi")],
                dtype=float,
            )
            accum["style"] = BoxStyle.ORTHOGONAL
        elif "abc origin" in header:
            cell = np.empty((3, 4), dtype=float)
            cell[:, :3] = np.array(
                [header[row].split() for row in ("avec", "bvec", "cvec")], dtype=float
            )
            cell[:, 3] = header["abc origin"].split()
            accum["style"] = BoxStyle.TRICLINIC
        else:
            raise LAMMPSConfigFileError(
                "Failed to find unit cell in configuration file."
            )

        accum["unit_cell"], accum["origin"] = accum["style"].to_cell(cell)

        return accum

    _BOND_RESTRICT = {
        "atomic",
        "body",
        "charge",
        "dipole",
        "dpd",
        "edpd",
        "electron",
        "ellipsoid",
        "line",
        "mdpd",
        "oxdna",
        "perismdrheo",
        "rheo/thermal",
        "sph",
        "sphere",
        "spin",
        "tdpd",
        "template",
        "tri",
        "wavepacket",
    }
    _BOND_RESTRICT |= {f"{key}_w_image" for key in _BOND_RESTRICT}
    _ANGLE_RESTRICT = {"bond", "bpm/sphere"}
    _ANGLE_RESTRICT |= {f"{key}_w_image" for key in _ANGLE_RESTRICT}
    _IMPROPER_RESTRICT = {"angle"}
    _IMPROPER_RESTRICT |= {f"{key}_w_image" for key in _IMPROPER_RESTRICT}

    @staticmethod
    def _guess_type(word: str) -> type:
        """Quick guess at what type `word` represents.

        Since ``issubclass(bool, int) is True`` can blindly
        return ``bool``.

        Parameters
        ----------
        word : str
            Word from line.

        Returns
        -------
        type
            Best guess at type.

        Examples
        --------
        >>> ConfigFileConfigurator._guess_type("0")
        <class 'bool'>
        >>> ConfigFileConfigurator._guess_type("1.3")
        <class 'float'>
        >>> ConfigFileConfigurator._guess_type("17")
        <class 'int'>
        >>> ConfigFileConfigurator._guess_type("Hello")
        <class 'str'>
        """
        if word in "01":
            return bool
        if re.fullmatch(INTNUMBER_RE, word):
            return int
        if re.fullmatch(EXPFNUMBER_RE, word):
            return float
        return str

    def _guess_atom_type(self, line: str):
        """Attempt to guess atom type given current knowledge.

        Parameters
        ----------
        line : str
            Example line from config.
        """
        words = line.split()
        n_elem = len(words)
        types = list(map(self._guess_type, words))

        # Cannot distinguish these due to variable length.
        excl = {"tdpd", "hybrid", "tdpd_w_image", "hybrid_w_image"}

        if "Bonds" in self._known_blocks:
            excl |= self._BOND_RESTRICT
        if "Angles" in self._known_blocks:
            excl |= self._BOND_RESTRICT | self._ANGLE_RESTRICT
        if "Impropers" in self._known_blocks:
            excl |= self._BOND_RESTRICT | self._ANGLE_RESTRICT | self._IMPROPER_RESTRICT

        keys = (
            key
            for key in ATOM_TYPES_MAP
            if key not in excl and len(ATOM_TYPES_MAP[key]) == n_elem
        )

        for key in keys:
            trial_atom_type = ATOM_TYPES_MAP[key]
            trial_var_types = (
                first(
                    val
                    for key_re, val in KEY_TYPES_MAP.items()
                    if re.fullmatch(key_re, name)
                )
                for name in trial_atom_type
            )

            # Assume first one is right one.
            if all(map(issubclass, types, trial_var_types)):
                return key

        raise LAMMPSConfigFileError("Cannot guess atom type.")

    def atoms_parser(
        self, lines: Iterable[str], atom_type: AtomTypes | None = None
    ) -> dict:
        """Parse atoms block.

        If header does not contain atoms or atom types will set those.

        Parameters
        ----------
        lines : Iterable[str]
            Lines to parse.
        atom_type : Optional[AtomTypes]
            Atom type if known.

        Raises
        ------
        LAMMPSConfigFileError
            Header data does not match.

        See Also
        --------
        ConfigFileConfigurator._guess_atom_type : Mechanism for guessing atom type.
        """
        lines = filter(None, lines)
        trial, lines = spy(lines)

        parsed = {}

        # User defined atom type takes priority.
        if self.get("atom_type", "From config") != "From config":
            atom_type = self["atom_type"]

        if atom_type and atom_type != "unknown":
            if len(trial[0].split()) == len(ATOM_TYPES_MAP[atom_type]) + 3:
                atom_type += "_w_image"
        else:
            LOG.warning(
                "Unidentified or non-matching atom type (%r). Attempting to determine.",
                atom_type,
            )

            atom_type = self._guess_atom_type(trial[0])

        LOG.info("Atom type determined to be: %r", atom_type)

        atom_style = ATOM_TYPES_MAP[atom_type]
        AtomData = namedtuple("AtomData", atom_style)
        lines = strip_comments(lines)
        atom_data = list(starmap(AtomData, map(str.split, lines)))

        parsed["n_atoms"] = self.get("n_atoms", len(atom_data))

        if len(atom_data) != parsed["n_atoms"]:
            raise LAMMPSConfigFileError(
                f"Data mismatch between n_atoms in header ({parsed['n_atoms']}) and atoms in file ({len(atom_data)})."
            )

        parsed["atom_types"] = np.array(
            [atom.atom_type for atom in atom_data], dtype=int
        )

        parsed["n_atom_types"] = self.get("n_atom_types", parsed["atom_types"].max())
        if parsed["atom_types"].max() > parsed["n_atom_types"]:
            raise LAMMPSConfigFileError(
                f"Data mismatch between n_atom_types in header ({parsed['n_atom_types']}) and in block ({parsed['atom_types'].max()})"
            )

        if "q" in atom_style:
            parsed["charges"] = np.array([atom.q for atom in atom_data], dtype=float)

        return parsed

    def bonds_parser(
        self, lines: Iterable[str], *_
    ) -> dict[Literal["bonds"], Sequence[tuple[int, int]]]:
        """Parse bonded atoms.

        Parameters
        ----------
        lines : Iterable[str]
            Block containing bonds data.


        """
        bonds = [tuple(elems[1:]) for elems in int_list_parser(lines).values()]

        if len(bonds) != self["n_bonds"]:
            raise LAMMPSConfigFileError(
                f"Data mismatch between n_bonds in header ({self['n_bonds']}) and in block ({len(bonds)})"
            )

        return {"bonds": bonds}

    def mass_parser(
        self, lines: Iterable[str], *_
    ) -> dict[Literal["mass"], NDArray[float]]:
        """Get atom-type masses.

        Parameters
        ----------
        lines : Iterable[str]
            Block containing mass data.
        """

        # ASE/VMD dumps element as comment on masses (VMD doesn't respect case)
        element_map = {
            int(line.split()[0]): match[1].title()
            for line in lines
            if (match := re.search(r"# ([A-Z][a-z]{,2})\s*$", line, re.I))
        }

        if element_map and self.setdefault("elements", element_map) != element_map:
            LOG.warning(
                f"Mismatch between determined element names ({', '.join(element_map.values())}) "
                f" and existing element names ({', '.join(self['elements'].values())})."
            )

        return {
            "mass": np.array(
                [elem[0] for elem in float_list_parser(lines).values()], dtype=float
            )
        }

    def elements_parser(
        self, lines: Iterable[str], *_
    ) -> dict[Literal["elements"], dict[int, str]]:
        """Parse elements block.

        Parameters
        ----------
        lines : Iterable[str]
            Block containing atom type labels data.
        """
        return {
            "elements": {
                int(key): val
                for key, val in one_to_one_parser(filter(None, lines)).items()
            }
        }

    #: How to parse different blocks.
    #:
    #: **N.B.** If parser does not set ``self`` or block not in ``DESIRED``,
    #: will do nothing.
    BLOCK_PARSERS = {
        "header": header_parser,
        "Atoms": atoms_parser,
        "Bonds": bonds_parser,
        "Masses": mass_parser,
        "Atom Type Labels": elements_parser,
        # Parse guesses for future implementation if needed.
        # **dict.fromkeys(("Bond Type Labels", "Angle Type Labels",
        #                  "Dihedral Type Labels", "Improper Type Labels"), one_to_one_parser),
        # **dict.fromkeys(("Angles", "Dihedrals", "Impropers"), int_list_parser),
        # **dict.fromkeys(("Pair Coeffs", "PairIJ Coeffs", "Bond Coeffs",
        #                   "Angle Coeffs", "Dihedral Coeffs", "Improper Coeffs",
        #                   "BondBond Coeffs", "BondAngle Coeffs",
        #                   "MiddleBondTorsion Coeffs", "EndBondTorsion Coeffs",
        #                   "AngleTorsion Coeffs", "AngleAngleTorsion Coeffs",
        #                   "BondBond13 Coeffs", "AngleAngle Coeffs"), float_list_parser),
    }

    _is_block = re.compile("^[A-Z]").match

    @staticmethod
    def scan(filename: Path | str) -> list[str]:
        """Scan file to work out which blocks are present.

        Parameters
        ----------
        filename : Path | str
            Filename to scan.

        Returns
        -------
        list[str]
            Blocks present in file.
        """
        with open(filename, encoding="utf-8") as source_file:
            return [
                line.strip()
                for line in strip_comments(source_file)
                if ConfigFileConfigurator._is_block(line)
            ]

    def parse(self, filename: Path | str | None = None) -> None:
        """Parse file and store data in self."""
        self._filename = self["filename"] if filename is None else filename

        self._known_blocks = self.scan(self._filename)

        with open(self._filename, encoding="utf-8") as source_file:
            lines = map(str.strip, source_file)

            comment = next(lines)
            (line,), lines = spy(lines)

            # Fix for VMD disobeying spec.
            if not re.match(r"\s*\d+\s+atoms", line, re.I):
                comment += " " + next(lines)

            for desc in re.finditer(r"(\w+)\s*=\s*(\w+)", comment):
                self[desc[1]] = desc[2]
            if "units" in self:
                LOG.info("Units determined to be %r", self["units"])

            blocks = split_before(lines, self._is_block)
            header = next(blocks)

            self.update(self.header_parser(header))

            for block in blocks:
                block_type, *comment = map(str.strip, block[0].split("#"))
                if block_type not in DESIRED:
                    continue

                self.update(self.BLOCK_PARSERS[block_type](self, block[2:], *comment))

        elem_range = range(1, self["n_atom_types"] + 1)

        self.setdefault("elements", dict(zip(elem_range, map(str, elem_range))))
        self.setdefault("charges", np.zeros(self["n_atoms"]))

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        conts = sorted(self.keys() & {"elements", "mass"})
        if conts == ["elements", "mass"]:
            for elem, mass in zip(self["elements"].values(), self["mass"]):
                yield AtomLabel(elem, mass=mass)
        elif conts == ["elements"]:
            for elem in self["elements"].values():
                yield AtomLabel(elem)
        elif conts == ["mass"]:
            for idx, mass in enumerate(self["mass"], 1):
                yield AtomLabel(str(idx), mass=mass)
        else:
            for idx in range(self["n_atom_types"]):
                yield AtomLabel(str(idx))
