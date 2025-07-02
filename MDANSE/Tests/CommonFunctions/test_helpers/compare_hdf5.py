from collections.abc import Sequence
from pathlib import Path
from typing import Tuple, Union

import h5py
import numpy as np


def compare_hdf5(
    result_path: Path,
    benchmark_path: Path,
    comparison_keys: Sequence[str],
    *,
    atol: float = 1e-10,
    rtol: float = 1e-7,
    startswith: bool = False,
    scale_result: bool = False,
    scale_benchmark: bool = False,
) -> None:
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
    scale_result : bool
        Whether result should be scaled.
    scale_benchmark : bool
        Whether benchmark should be scaled.
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

            if isinstance(result[f"/{key}"], h5py.Dataset):
                search = (key,)
            else:
                # Recursive search through all datasets.
                search = []

                def visitor(name: str, obj: type):
                    if isinstance(obj, h5py.Dataset) and "axes" not in name:
                        search.append(f"{key}/{name}")

                result[f"/{key}"].visititems(visitor)

            assert search, f"No keys matching search term '{key}' found"

            for test in search:
                assert test in result, f"Key ({test}) not found in result."
                assert test in benchmark, f"Key ({test}) not found in benchmark."

                a = (
                    result[f"/{test}"] * result[f"/{test}"].attrs["scaling_factor"]
                    if scale_result
                    else result[f"/{test}"]
                )
                b = (
                    benchmark[f"/{test}"][subset]
                    * benchmark[f"/{test}"].attrs["scaling_factor"]
                    if scale_benchmark
                    else benchmark[f"/{test}"][subset]
                )

                np.testing.assert_allclose(
                    a, b, atol=atol, rtol=rtol, err_msg=f"Failure in key {test!r}."
                )
