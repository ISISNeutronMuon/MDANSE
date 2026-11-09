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

import json
import re
from datetime import datetime
from math import pi, sqrt
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

import MDANSE
from MDANSE import PLATFORM
from MDANSE.Framework.AtomGrouping.grouping import pair_labels
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.UnitCell import CELL_SIZE_LIMIT

if TYPE_CHECKING:
    import h5py

    from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
    from MDANSE.util_types import FloatArray

# Conversion factors from the MDANSE internal units to the McStas units.
#: hbar in meV ps, converts angular frequencies (rad/ps) to energies (meV).
_MEV_PER_RAD_PS = measure(1.0, "rad/ps", equivalent=True).toval("meV")
_INV_NM_TO_INV_ANG = measure(1.0, "1/nm").toval("1/ang")
_ANG2_TO_BARN = measure(1.0, "ang2").toval("barn")
_NM2_TO_BARN = measure(1.0, "nm2").toval("barn")
_NM3_TO_ANG3 = measure(1.0, "nm3").toval("ang3")
#: Avogadro constant in 1/mol (exact value of the SI definition).
_AVOGADRO = 6.02214076e23
_ANG3_PER_CM3 = 1.0e24

_KINDS = ("dcsf", "disf")
_KIND = {"coh": "dcsf", "inc": "disf"}
_PART_NAME = {"coh": "coherent", "inc": "incoherent"}

#: Header keywords that the McStas Isotropic_Sqw component searches for.
#: They are broken up in the free-text header lines, so that McStas only
#: reads the values written on purpose.
_HEADER_KEYWORDS = re.compile(
    r"vc|v_0|v0|sigma_|column_|temperature|v_rho|density|weight|nb_atoms"
    r"|multiplicity|classical",
    re.IGNORECASE,
)
#: Largest number of points of an axis interpolated on an evenly spaced grid.
_MAX_GRID_POINTS = 10000


class McStasSqwExportError(Exception):
    pass


def _normalise_setting(value: Any) -> Any:
    """Decode a job input stored in the metadata of an MDANSE file.

    Parameters
    ----------
    value : Any
        JSON text (str or bytes), as stored in ``metadata/inputs`` or
        returned by ``IConfigurator.to_json``.

    Returns
    -------
    Any
        The decoded value. Empty values (None, empty strings and empty
        containers) are returned as None.
    """
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    # Inputs given as JSON text are encoded twice.
    for _ in range(2):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except ValueError:
            break
    if value in (None, "", {}, []):
        return None
    return value


def _sanitise(text: str) -> str:
    """Make a line of free text safe for the header of a McStas file.

    Whitespace is collapsed, non-ASCII characters are replaced and the
    keywords that McStas searches for in the header are broken up with a
    tilde, so that they cannot be read as header values.

    Parameters
    ----------
    text : str
        Line of free text.

    Returns
    -------
    str
        The sanitised line.
    """
    text = " ".join(text.split())
    text = text.encode("ascii", errors="replace").decode("ascii")
    return _HEADER_KEYWORDS.sub(lambda match: f"{match[0][0]}~{match[0][1:]}", text)


def _format_values(values: FloatArray, limit: int = 10) -> str:
    """Format the first values of an array for a log message.

    Parameters
    ----------
    values : FloatArray
        Values to format.
    limit : int
        Largest number of values written out.

    Returns
    -------
    str
        Comma-separated values.
    """
    values = np.ravel(values)
    text = ", ".join(f"{value:.4g}" for value in values[:limit])
    if values.size > limit:
        text += f", ... ({values.size} values)"
    return text


def _interpolate_rows(
    x_new: FloatArray, x: FloatArray, values: FloatArray
) -> FloatArray:
    """Interpolate the rows of a 2D array linearly.

    Parameters
    ----------
    x_new : FloatArray
        Positions of the new rows, within the range of x.
    x : FloatArray
        At least 2 strictly increasing positions of the rows of values.
    values : FloatArray
        2D array with one row per value of x.

    Returns
    -------
    FloatArray
        2D array with one row per value of x_new.
    """
    upper = np.clip(np.searchsorted(x, x_new), 1, x.size - 1)
    lower = upper - 1
    weight = ((x_new - x[lower]) / (x[upper] - x[lower]))[:, np.newaxis]
    return (1.0 - weight) * values[lower] + weight * values[upper]


def _even_grid(axis: FloatArray) -> FloatArray | None:
    """Create an evenly spaced grid over the range of an axis.

    Parameters
    ----------
    axis : FloatArray
        Strictly increasing values.

    Returns
    -------
    FloatArray | None
        Evenly spaced values from the first to the last value of the
        axis, with a step close to the smallest step of the axis, or None
        if the axis is already evenly spaced.
    """
    steps = np.diff(axis)
    if steps.size == 0 or np.allclose(steps, steps.mean(), rtol=1e-4, atol=0.0):
        return None
    n_points = round(float((axis[-1] - axis[0]) / steps.min())) + 1
    n_points = min(max(n_points, axis.size), _MAX_GRID_POINTS)
    return np.linspace(axis[0], axis[-1], n_points)


@IJob.register("McStasSqwExport")
class McStasSqwExport(IJob):
    """Exports dynamic structure factors to the McStas ``Isotropic_Sqw`` format.

    Converts the results of the Dynamic Coherent Structure Factor (DCSF)
    and Dynamic Incoherent Structure Factor (DISF) analyses into the text
    files read by the ``Isotropic_Sqw`` sample component of the McStas
    neutron ray-tracing package. At least one of the two results is needed.
    The trajectory, atom selection, atom transmutation and grouping level
    must be the same as in the DCSF and DISF runs.

    The coherent part is written to ``OUTPUT_coh.sqw`` and the incoherent
    part to ``OUTPUT_inc.sqw``, where OUTPUT is the output file name without
    extension. The ``.sqw`` files are written whichever output formats are
    selected. The exported data are also saved in the MDANSE output file,
    under ``mcstas/``.

    The scattering unit is one atom, averaged over the selected atoms. The
    partial spectra are weighted with the neutron scattering lengths b and
    divided by the average of b squared, so that the energy integral of the
    coherent S(q,w) tends to 1 at large q and the incoherent S(q,w)
    integrates to 1 over energy. The coherent part is therefore not the same
    as the total DCSF of MDANSE, which is divided by the square of the
    average b. The file headers give the matching cross-sections per atom,
    the absorption cross-section, the temperature, the number density of
    atoms (from the average unit cell volume) and the mass density. The q
    values are converted to 1/Angstrom, the energies to meV and S(q,w) to
    1/meV. Points at q = 0 are removed, rows with NaN or infinite values are
    removed or interpolated, axes that are not evenly spaced are
    interpolated on an evenly spaced grid and negative values are set to
    zero.

    MD simulations give a classical, symmetric S(q,w). The files are marked
    as classical and contain the sample temperature, so that McStas can
    apply the detailed balance factor.

    By default, the spectra calculated without the MDANSE instrument
    resolution are exported when the input files contain them, so that only
    the simulated McStas instrument adds a resolution.

    In McStas, use the files in an ``Isotropic_Sqw`` component with
    ``norm=0`` to keep the absolute normalisation. A complete component
    definition is written to the job log. The format follows the McStas
    documentation, but please check the values reported by McStas the first
    time you use the files.
    """

    enabled = True

    label = "McStas Sqw Export"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["dcsf_input_file"] = (
        "HDFInputFileConfigurator",
        {
            "label": "Coherent structure factor (DCSF .mda, optional)",
            "default": "",
            "optional": True,
            "tooltip": (
                "Result of the DynamicCoherentStructureFactor analysis on the "
                "input trajectory. Leave empty to export only the incoherent part."
            ),
        },
    )
    settings["disf_input_file"] = (
        "HDFInputFileConfigurator",
        {
            "label": "Incoherent structure factor (DISF .mda, optional)",
            "default": "",
            "optional": True,
            "tooltip": (
                "Result of the DynamicIncoherentStructureFactor analysis on the "
                "input trajectory. Leave empty to export only the coherent part."
            ),
        },
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_transmutation"] = (
        "AtomTransmutationConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
    )
    settings["temperature"] = (
        "FloatConfigurator",
        {
            "mini": 0.0,
            "default": 300.0,
            "label": "Sample temperature (K)",
            "tooltip": (
                "Temperature of the simulated sample. McStas uses it to apply "
                "the detailed balance factor to the classical MD spectra."
            ),
        },
    )
    settings["use_ideal_spectra"] = (
        "BooleanConfigurator",
        {
            "default": True,
            "label": "Use spectra without instrument resolution",
            "tooltip": (
                "Export the spectra calculated without the MDANSE instrument "
                "resolution, if the input files contain them. The McStas "
                "instrument then adds its own resolution."
            ),
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})

    def initialize(self):
        """Check the inputs and read the spectra into memory."""
        super().initialize()

        self.numberOfSteps = 1

        try:
            self._read_inputs()
        except Exception:
            self.trajectory.close()
            raise
        finally:
            for kind in _KINDS:
                instance = self.configuration[f"{kind}_input_file"].get("instance")
                if instance is not None:
                    instance.close()

    def _read_inputs(self):
        """Check the inputs and read the axes and the partial spectra.

        Raises
        ------
        McStasSqwExportError
            If the inputs cannot be used.
        """
        self._temperature = float(self.configuration["temperature"]["value"])
        if not self._temperature > 0.0:
            raise McStasSqwExportError(
                "The sample temperature must be larger than 0 K. McStas needs it "
                "to apply the detailed balance factor to the classical MD spectra."
            )

        files = {}
        for kind in _KINDS:
            conf = self.configuration[f"{kind}_input_file"]
            if not conf.valid:
                raise McStasSqwExportError(self._input_file_error(kind, conf))
            if conf.get("instance") is not None:
                files[kind] = conf["instance"]
        if not files:
            raise McStasSqwExportError(
                "No input file given. Select the result of a DCSF analysis, "
                "of a DISF analysis, or both."
            )

        self._n_atoms = dict(self.trajectory.get_natoms())
        if sum(self._n_atoms.values()) <= 0:
            raise McStasSqwExportError("No atoms are selected.")
        self._element_from_label = self.trajectory.element_from_label
        self._pairs = pair_labels(self.trajectory)

        self._spectra = {}
        self._sources = {}
        self._resolution = {}
        axes = {}
        for kind, h5 in files.items():
            self._check_settings(kind, h5)
            axes[kind] = self._read_axes(kind, h5)
            self._spectra[kind] = self._read_spectra(kind, h5, axes[kind])
            self._sources[kind] = Path(h5.filename).stem

        if len(axes) > 1 and not all(
            self._same_axis(first, second)
            for first, second in zip(axes["dcsf"], axes["disf"], strict=True)
        ):
            raise McStasSqwExportError(
                "The DCSF and DISF results have different q or frequency axes. "
                "Calculate them with the same q vectors and frames."
            )
        self._q, self._omega = next(iter(axes.values()))
        self._volume = self._mean_volume()

    @staticmethod
    def _input_file_error(kind: str, conf: IConfigurator) -> str:
        """Explain why an input file cannot be used.

        Parameters
        ----------
        kind : str
            Type of the input file, "dcsf" or "disf".
        conf : IConfigurator
            Configurator of the input file.

        Returns
        -------
        str
            The error message.
        """
        path = Path(conf.get("value", ""))
        if not path.is_file():
            return f"The {kind.upper()} input file {path} does not exist."
        return (
            f"The {kind.upper()} input file {path} could not be opened. It must "
            "be the result of an MDANSE analysis (.mda file)."
        )

    def _check_settings(self, kind: str, h5: h5py.File):
        """Compare the job settings with the ones used to create an input file.

        Parameters
        ----------
        kind : str
            Type of the input file, "dcsf" or "disf".
        h5 : h5py.File
            The input file.

        Raises
        ------
        McStasSqwExportError
            If the atom selection is different.
        """
        name = kind.upper()
        stored = h5.get("selected_atoms")
        current = self._outputData.get("selected_atoms")
        if stored is None or current is None:
            LOG.warning(
                f"Could not check that the atom selection is the same as in the "
                f"{name} run. Make sure that the same atoms are selected."
            )
        elif not np.array_equal(
            np.asarray(stored[()], dtype=bool), np.asarray(current, dtype=bool)
        ):
            raise McStasSqwExportError(
                f"The atom selection is different from the one used in the {name} "
                "run. Use the same trajectory and atom selection."
            )

        for setting in ("atom_transmutation", "grouping_level"):
            try:
                stored_value = _normalise_setting(h5[f"metadata/inputs/{setting}"][0])
            except (KeyError, IndexError, ValueError):
                continue
            current_value = _normalise_setting(self.configuration[setting].to_json())
            if stored_value != current_value:
                LOG.warning(
                    f"The {setting.replace('_', ' ')} ({current_value}) is "
                    f"different from the one used in the {name} run "
                    f"({stored_value}). The exported spectra may be inconsistent."
                )

    @staticmethod
    def _read_axes(kind: str, h5: h5py.File) -> tuple[FloatArray, FloatArray]:
        """Read the q axis (1/nm) and the frequency axis (rad/ps) of a result.

        Parameters
        ----------
        kind : str
            Type of the input file, "dcsf" or "disf".
        h5 : h5py.File
            The input file.

        Returns
        -------
        tuple[FloatArray, FloatArray]
            The q values and the angular frequencies.

        Raises
        ------
        McStasSqwExportError
            If the file does not contain results of the expected analysis.
        """
        try:
            q = np.array(h5[f"{kind}/axes/q"], dtype=float)
            omega = np.array(h5[f"{kind}/axes/omega"], dtype=float)
        except KeyError:
            raise McStasSqwExportError(
                f"The file {Path(h5.filename).name} does not contain "
                f"{kind.upper()} results. Check that it was put in the right "
                "input field."
            ) from None
        return q, omega

    def _read_spectra(
        self, kind: str, h5: h5py.File, axes: tuple[FloatArray, FloatArray]
    ) -> dict[str, FloatArray]:
        """Read the partial spectra needed for the coherent or incoherent part.

        Parameters
        ----------
        kind : str
            Type of the input file, "dcsf" or "disf".
        h5 : h5py.File
            The input file.
        axes : tuple[FloatArray, FloatArray]
            The q and frequency axes of the file.

        Returns
        -------
        dict[str, FloatArray]
            Partial S(q,f) arrays, without scaling, by pair or atom label.

        Raises
        ------
        McStasSqwExportError
            If partial spectra are missing or cannot be used.
        """
        name = kind.upper()
        group = f"{kind}/s(q,f)"
        if kind == "dcsf":
            labels = [pair for pair, _ in self._pairs]
        else:
            labels = sorted(self._n_atoms)

        missing = [label for label in labels if f"{group}/{label}" not in h5]
        if missing:
            raise McStasSqwExportError(
                f"The {name} file does not contain the partial spectra "
                f"{', '.join(missing)}. The trajectory, atom selection, atom "
                "transmutation and grouping level must be the same as in the "
                f"{name} run."
            )

        shape = (axes[0].size, axes[1].size)
        for label in labels:
            dataset = h5[f"{group}/{label}"]
            if "scaling_factor" not in dataset.attrs:
                raise McStasSqwExportError(
                    f"This {name} file was created before the new scaling scheme. "
                    "Please calculate it again."
                )
            if dataset.shape != shape:
                raise McStasSqwExportError(
                    f"The partial spectrum {label} of the {name} file has the "
                    f"shape {dataset.shape} instead of {shape}."
                )

        prefix = self._choose_spectra(kind, h5, labels)
        return {
            label: np.array(h5[f"{group}/{prefix}{label}"], dtype=float)
            for label in labels
        }

    def _choose_spectra(self, kind: str, h5: h5py.File, labels: list[str]) -> str:
        """Choose the spectra with or without MDANSE instrument resolution.

        Parameters
        ----------
        kind : str
            Type of the input file, "dcsf" or "disf".
        h5 : h5py.File
            The input file.
        labels : list[str]
            Labels of the partial spectra.

        Returns
        -------
        str
            Prefix of the datasets to read, relative to the S(q,f) group.
        """
        name = kind.upper()
        kernel = self._resolution_kernel(h5)
        has_ideal = all(f"{kind}/s(q,f)/ideal/{label}" in h5 for label in labels)

        if has_ideal and self.configuration["use_ideal_spectra"]["value"]:
            self._resolution[kind] = "not included (spectra without resolution)"
            LOG.info(
                f"Using the {name} spectra calculated without instrument resolution."
            )
            return "ideal/"

        if kernel is None:
            self._resolution[kind] = "unknown"
        elif kernel == "ideal":
            self._resolution[kind] = "none"
        else:
            self._resolution[kind] = f"included ({kernel})"
            advice = (
                ""
                if has_ideal
                else f" Use the ideal resolution in the {name} analysis to avoid it."
            )
            LOG.warning(
                f"The exported {name} spectra include the MDANSE instrument "
                f"resolution ({kernel}). The McStas instrument will add its own "
                f"resolution on top of it.{advice}"
            )
        return ""

    @staticmethod
    def _resolution_kernel(h5: h5py.File) -> str | None:
        """Read the name of the instrument resolution kernel of a result.

        Parameters
        ----------
        h5 : h5py.File
            The input file.

        Returns
        -------
        str | None
            The kernel name in lower case, or None if it is not known.
        """
        try:
            setting = _normalise_setting(h5["metadata/inputs/instrument_resolution"][0])
        except (KeyError, IndexError, ValueError):
            return None
        if isinstance(setting, list) and setting:
            setting = setting[0]
        return setting.lower() if isinstance(setting, str) else None

    @staticmethod
    def _same_axis(first: FloatArray, second: FloatArray) -> bool:
        """Check whether two axes have the same values."""
        return first.shape == second.shape and bool(
            np.allclose(first, second, rtol=1e-6, atol=0.0)
        )

    def _mean_volume(self) -> float | None:
        """Calculate the average unit cell volume of the trajectory.

        Returns
        -------
        float | None
            The volume in nm3, or None if the unit cell is not defined.
        """
        n_frames = len(self.trajectory)
        frames = np.unique(
            np.linspace(0, n_frames - 1, min(n_frames, 1000)).astype(int)
        )
        volumes = []
        for frame in frames:
            cell = self.trajectory.unit_cell(int(frame))
            if cell is None or not cell.volume > CELL_SIZE_LIMIT:
                LOG.warning(
                    "The trajectory has no valid unit cell, so the number density "
                    "of atoms is unknown. Set the rho parameter of Isotropic_Sqw "
                    "in McStas."
                )
                return None
            volumes.append(cell.volume)
        mean = float(np.mean(volumes))
        spread = float(np.std(volumes)) / mean
        if spread > 1e-6:
            LOG.info(
                f"The unit cell volume changes during the trajectory (relative "
                f"standard deviation {spread:.3g}). The average volume is used."
            )
        return mean

    def _atom_property(self, label: str, prop: str) -> complex:
        """Read an atom property for an atom label.

        Parameters
        ----------
        label : str
            Atom label, as used in the partial spectra.
        prop : str
            Name of the property in the atom database.

        Returns
        -------
        complex
            The value of the property.

        Raises
        ------
        McStasSqwExportError
            If the property is not a number.
        """
        element = self._element_from_label.get(label, label)
        try:
            return complex(self.trajectory.get_atom_property(element, prop))
        except (KeyError, ValueError, TypeError) as err:
            raise McStasSqwExportError(
                f"Could not read the property {prop} of the atom type {element} "
                "from the atom database."
            ) from err

    def _average_property(self, prop: str) -> float:
        """Average a real atom property over the selected atoms."""
        total = sum(
            number * self._atom_property(label, prop).real
            for label, number in self._n_atoms.items()
        )
        return total / sum(self._n_atoms.values())

    def run_step(self, index: int) -> tuple[int, None]:
        """Do nothing, the files are converted in finalize.

        Parameters
        ----------
        index : int
            The index of the step.

        Returns
        -------
        tuple[int, None]
            The index of the step and no result.
        """
        return index, None

    def combine(self, index: int, x: None):
        """Do nothing, run_step returns no result.

        Parameters
        ----------
        index : int
            The index of the step.
        x : None
            The result of run_step.
        """

    def finalize(self):
        """Write the McStas files and the MDANSE output file."""
        try:
            self._export()
        finally:
            self.trajectory.close()
        super().finalize()

    def _coherent_part(self) -> tuple[FloatArray, float] | None:
        """Combine the DCSF partial spectra into a coherent S(q,f) per atom.

        Returns
        -------
        tuple[FloatArray, float] | None
            The coherent S(q,f), whose energy integral tends to 1 at large
            q, and the coherent cross-section per atom in barn, or None if
            the selected atoms do not scatter coherently.
        """
        b_coh = {
            label: self._atom_property(label, "b_coherent") for label in self._n_atoms
        }
        norm = sum(
            number * abs(b_coh[label]) ** 2 for label, number in self._n_atoms.items()
        )
        if not norm > 0.0:
            LOG.warning(
                "The selected atoms have no coherent scattering length. The "
                "coherent part is not exported."
            )
            return None

        partials = self._spectra["dcsf"]
        total = np.zeros_like(next(iter(partials.values())))
        for pair, (label_i, label_j) in self._pairs:
            factor = 1.0 if label_i == label_j else 2.0
            weight = (
                factor
                * (b_coh[label_i].conjugate() * b_coh[label_j]).real
                * sqrt(self._n_atoms[label_i] * self._n_atoms[label_j])
            )
            total += weight * partials[pair]
        sigma = 4.0 * pi * norm / sum(self._n_atoms.values()) * _ANG2_TO_BARN
        return total / norm, sigma

    def _incoherent_part(self) -> tuple[FloatArray, float] | None:
        """Combine the DISF partial spectra into an incoherent S(q,f) per atom.

        Returns
        -------
        tuple[FloatArray, float] | None
            The incoherent S(q,f), which integrates to 1 over energy, and
            the incoherent cross-section per atom in barn, or None if the
            selected atoms do not scatter incoherently.
        """
        b_inc = {
            label: self._atom_property(label, "b_incoherent") for label in self._n_atoms
        }
        norm = sum(
            number * abs(b_inc[label]) ** 2 for label, number in self._n_atoms.items()
        )
        if not norm > 0.0:
            LOG.warning(
                "The selected atoms have no incoherent scattering length. The "
                "incoherent part is not exported."
            )
            return None

        partials = self._spectra["disf"]
        total = np.zeros_like(next(iter(partials.values())))
        for label, number in self._n_atoms.items():
            total += number * abs(b_inc[label]) ** 2 * partials[label]
        sigma = 4.0 * pi * norm / sum(self._n_atoms.values()) * _ANG2_TO_BARN
        return total / norm, sigma

    def _export(self):
        """Combine the partial spectra and write the McStas and MDANSE files.

        Raises
        ------
        McStasSqwExportError
            If there is nothing to export.
        """
        parts = {}
        if "dcsf" in self._spectra:
            parts["coh"] = self._coherent_part()
        if "disf" in self._spectra:
            parts["inc"] = self._incoherent_part()
        parts = {part: result for part, result in parts.items() if result is not None}
        if not parts:
            raise McStasSqwExportError(
                "Nothing to export: the selected atoms do not scatter neutrons."
            )

        sigmas = {f"sigma_{part}": sigma for part, (_, sigma) in parts.items()}
        sigma_abs = self._average_property("xs_absorption") * _NM2_TO_BARN
        weight = self._average_property("atomic_weight")
        rho = None
        if self._volume is not None:
            rho = sum(self._n_atoms.values()) / (self._volume * _NM3_TO_ANG3)

        common = {
            "sigma_abs": (sigma_abs, "[barn]"),
            "Temperature": (self._temperature, "[K]"),
        }
        if rho is not None:
            common["V_rho"] = (rho, "[Angs-3]")
            common["density"] = (weight * rho * _ANG3_PER_CM3 / _AVOGADRO, "[g/cm3]")
        common["weight"] = (weight, "[g/mol]")
        common["classical"] = (1, "")

        q, energy, spectra = self._clean_spectra(
            self._q * _INV_NM_TO_INV_ANG,
            self._omega * _MEV_PER_RAD_PS,
            {part: sqw / _MEV_PER_RAD_PS for part, (sqw, _) in parts.items()},
        )

        self._outputData.add("mcstas/axes/q", "LineOutputVariable", q, units="1/ang")
        self._outputData.add(
            "mcstas/axes/energy", "LineOutputVariable", energy, units="meV"
        )

        root = Path(self.configuration["output_files"]["root"])
        base = root.with_suffix("") if root.suffix.lower() == ".mda" else root
        PLATFORM.create_directory(base.parent)
        written = {}
        for part, sqw in spectra.items():
            self._outputData.add(
                f"mcstas/s(q,e)_{part}",
                "SurfaceOutputVariable",
                sqw,
                axis="mcstas/axes/q|mcstas/axes/energy",
                units="1/meV",
                main_result=True,
            )
            path = base.parent / f"{base.name}_{part}.sqw"
            keywords = {f"sigma_{part}": (sigmas[f"sigma_{part}"], "[barn]")}
            keywords.update(common)
            self._write_sqw_file(
                path, q, energy, sqw, self._description(part), keywords
            )
            written[part] = path.absolute()
            LOG.info(
                f"Wrote the {_PART_NAME[part]} S(q,w) for McStas to {written[part]}"
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )
        self._log_component(written, sigmas, sigma_abs, rho)

    @staticmethod
    def _clean_spectra(
        q: FloatArray, energy: FloatArray, spectra: dict[str, FloatArray]
    ) -> tuple[FloatArray, FloatArray, dict[str, FloatArray]]:
        """Prepare the grid and the spectra for McStas.

        Points with q <= 0 are removed. Rows of S(q,w) with NaN or infinite
        values are removed at the ends of the q range and interpolated
        linearly in q elsewhere. Axes that are not evenly spaced are
        interpolated on an evenly spaced grid. Negative values are set to 0.

        Parameters
        ----------
        q : FloatArray
            Increasing q values in 1/ang.
        energy : FloatArray
            Increasing energies in meV.
        spectra : dict[str, FloatArray]
            S(q,w) arrays in 1/meV, with one row per q value.

        Returns
        -------
        tuple[FloatArray, FloatArray, dict[str, FloatArray]]
            New arrays of q values, energies and S(q,w).

        Raises
        ------
        McStasSqwExportError
            If the axes cannot be used or fewer than 2 q values are left.
        """
        if not (np.all(np.isfinite(q)) and np.all(np.isfinite(energy))):
            raise McStasSqwExportError(
                "The q or energy axis contains NaN or infinite values."
            )
        if energy.size < 2 or np.any(np.diff(energy) <= 0.0):
            raise McStasSqwExportError(
                "The energy axis must contain at least 2 values in increasing order."
            )

        keep = q > 0.0
        if not np.all(keep):
            LOG.info(
                f"Removed {np.count_nonzero(~keep)} q value(s) <= 0, which "
                "McStas cannot use."
            )
        q = q[keep]
        spectra = {
            part: np.array(sqw[keep], dtype=float) for part, sqw in spectra.items()
        }
        if np.any(np.diff(q) <= 0.0):
            raise McStasSqwExportError("The q values must be in increasing order.")

        finite = {
            part: np.all(np.isfinite(sqw), axis=1) for part, sqw in spectra.items()
        }
        usable = np.flatnonzero(np.logical_and.reduce(list(finite.values())))
        if usable.size < 2:
            raise McStasSqwExportError(
                "Fewer than 2 q values have finite S(q,w) values, so nothing can "
                "be exported."
            )
        first, last = usable[0], usable[-1] + 1
        if first > 0 or last < q.size:
            removed = np.concatenate((q[:first], q[last:]))
            LOG.warning(
                f"Removed q = {_format_values(removed)} 1/ang at the ends of the "
                "q range, where S(q,w) contains NaN or infinite values."
            )
        q = q[first:last]

        cleaned = {}
        for part, sqw in spectra.items():
            rows = sqw[first:last].copy()
            good = finite[part][first:last]
            if not np.all(good):
                LOG.warning(
                    f"Interpolated the {_PART_NAME.get(part, part)} S(q,w) "
                    f"linearly in q at q = {_format_values(q[~good])} 1/ang, "
                    "where it contained NaN or infinite values."
                )
                rows[~good] = _interpolate_rows(q[~good], q[good], rows[good])
            cleaned[part] = rows
        spectra = cleaned

        new_q = _even_grid(q)
        if new_q is not None:
            LOG.warning(
                "The q values are not evenly spaced, as McStas expects. S(q,w) "
                f"was interpolated linearly on {new_q.size} evenly spaced q "
                f"values from {new_q[0]:.4g} to {new_q[-1]:.4g} 1/ang. Use evenly "
                "spaced q values in the DCSF and DISF analyses to avoid this."
            )
            spectra = {
                part: _interpolate_rows(new_q, q, sqw) for part, sqw in spectra.items()
            }
            q = new_q
        new_energy = _even_grid(energy)
        if new_energy is not None:
            LOG.warning(
                "The energies are not evenly spaced, as McStas expects. S(q,w) "
                f"was interpolated linearly on {new_energy.size} evenly spaced "
                "energies."
            )
            spectra = {
                part: _interpolate_rows(new_energy, energy, sqw.T).T
                for part, sqw in spectra.items()
            }
            energy = new_energy

        for part, sqw in spectra.items():
            negative = sqw < 0.0
            if np.any(negative):
                LOG.warning(
                    f"Set {np.count_nonzero(negative)} negative value(s) of the "
                    f"{_PART_NAME.get(part, part)} S(q,w) to 0 (lowest value "
                    f"{sqw.min():.3g} 1/meV), because McStas needs S(q,w) >= 0."
                )
                sqw[negative] = 0.0
        return q, energy, spectra

    def _description(self, part: str) -> list[str]:
        """Write the free-text header lines of an exported file.

        Parameters
        ----------
        part : str
            Exported part, "coh" or "inc".

        Returns
        -------
        list[str]
            Lines describing the origin of the data.
        """
        kind = _KIND[part]
        n_atoms = sum(self._n_atoms.values())
        counts = ", ".join(
            f"{label} {number}" for label, number in sorted(self._n_atoms.items())
        )
        trajectory = Path(self.trajectory.filename).stem
        return [
            f"Title: {_PART_NAME[part].capitalize()} S(q,w) from MDANSE for the "
            "McStas Isotropic_Sqw component",
            f"Creator: MDANSE {MDANSE.__version__} (McStasSqwExport)",
            f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"Source: {kind.upper()} result '{self._sources[kind]}', "
            f"trajectory '{trajectory}'",
            f"Scattering unit: one atom, average over {n_atoms} selected atoms "
            f"({counts})",
            f"MDANSE instrument resolution: {self._resolution[kind]}",
        ]

    @staticmethod
    def _write_sqw_file(
        path: Path,
        q: FloatArray,
        energy: FloatArray,
        sqw: FloatArray,
        description: list[str],
        keywords: dict[str, tuple[float, str]],
    ):
        """Write S(q,w) in the text format of the McStas Isotropic_Sqw component.

        Parameters
        ----------
        path : Path
            The output file.
        q : FloatArray
            The q values in 1/ang.
        energy : FloatArray
            The energies in meV.
        sqw : FloatArray
            S(q,w) in 1/meV, with one row per q value.
        description : list[str]
            Free-text header lines.
        keywords : dict[str, tuple[float, str]]
            Header values read by McStas, with their units.
        """
        lines = [
            "# Format: Sqw data file for Isotropic_Sqw <http://www.mcstas.org>",
            *(f"# {_sanitise(line)}" for line in description),
            *(
                f"# {key} {value:.8g} {unit}".rstrip()
                for key, (value, unit) in keywords.items()
            ),
            f"# WAVEVECTOR vector of {q.size} values in [Angs-1]",
            " ".join(f"{value:.10g}" for value in q),
            f"# ENERGY vector of {energy.size} values in [meV]",
            " ".join(f"{value:.10g}" for value in energy),
            f"# matrix of S(q,w) values ({q.size} rows x {energy.size} values) "
            "in [meV-1], one line per q value",
            *(" ".join(f"{value:.8e}" for value in row) for row in sqw),
        ]
        # McStas reads each block of the file in a separate pass, re-opening
        # the file in text mode and seeking to the ftell() position at which
        # the previous block ended. On Windows (MSVC runtime), ftell() in text
        # mode miscounts LF-only line endings, so the seek lands inside the
        # next data line and the energy axis is read wrongly (the simulation
        # can then allocate many GB and hang). With CRLF line endings the
        # offsets are exact, and on Linux/macOS the reader treats '\r' as a
        # separator, so CRLF works everywhere.
        path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\r\n")

    def _log_component(
        self,
        written: dict[str, Path],
        sigmas: dict[str, float],
        sigma_abs: float,
        rho: float | None,
    ):
        """Log an Isotropic_Sqw component definition using the exported files.

        Parameters
        ----------
        written : dict[str, Path]
            The exported files, by part.
        sigmas : dict[str, float]
            The scattering cross-sections in barn, by McStas parameter name.
        sigma_abs : float
            The absorption cross-section in barn.
        rho : float | None
            The number density of atoms in 1/ang3, if known.
        """
        arguments = [f'Sqw_{part}="{path.name}"' for part, path in written.items()]
        arguments.extend(f"{key}={value:.6g}" for key, value in sigmas.items())
        arguments.append(f"sigma_abs={sigma_abs:.6g}")
        if rho is not None:
            arguments.append(f"rho={rho:.6g}")
        arguments.extend(
            (
                f"T={self._temperature:.6g}",
                "classical=1",
                "norm=0",
                "radius=0.005",
                "yheight=0.05",
            )
        )
        lines = [
            "The exported files can be used in a McStas instrument, for example:",
            "COMPONENT sample = Isotropic_Sqw(",
            "    " + ",\n    ".join(arguments),
            ")",
            "AT (0, 0, 0) RELATIVE PREVIOUS",
            "Adjust the sample geometry and position, and put the .sqw files in "
            "the directory of the instrument.",
        ]
        if rho is None:
            lines.append(
                "The number density of atoms is unknown: add rho (atoms per "
                "cubic Angstrom) to the component."
            )
        if len(written) == 1:
            missing = "inc" if "coh" in written else "coh"
            lines.append(
                f"Only the {_PART_NAME[next(iter(written))]} part was exported. "
                f"The component does not set Sqw_{missing} or sigma_{missing}, "
                f"so McStas should not add any {_PART_NAME[missing]} scattering."
            )
        LOG.info("\n".join(lines))
