import numpy as np
from pathlib import Path
import h5py
from typing import Sequence

def compare_mdt(result_path: Path, benchmark_path: Path,
                comparison_keys: Sequence[str], *,
                startswith=False, normalised=False) -> None:
    """
    Compare two h5py files by the keys given in comparison_keys.

    Parameters
    ----------
    result_path : Path
        Path to output file from test run.
    benchmark_path : Path
        Path to benchmark results.
    comparison_keys : Sequence[str]
        List of keys to be present in outputs to compare.
    startswith : bool
        ``comparison_keys`` instead define a prefix of keys in ``result`` to check.
    normalised : bool
        Whether data should be normalised.
    """

    with h5py.File(result_path) as result, h5py.File(benchmark_path) as benchmark:

        if startswith:
            keys = (key for key in result.keys() if key.startswith(comparison_keys))
        else:
            keys = comparison_keys

        for key in keys:
            if isinstance(key, (tuple, list)):
                key, subset = key
            else:
                subset = slice(None)

            if normalised:
                np.testing.assert_array_almost_equal(
                    result[f"/{key}"] * result[f"/{key}"].attrs["scaling_factor"],
                    benchmark[f"/{key}"][subset],
                )
            else:
                np.testing.assert_array_almost_equal(
                    result[f"/{key}"], benchmark[f"/{key}"][subset],
                )
