import numpy as np
from pathlib import Path
import h5py
from typing import Sequence

def compare_mdt(result_path: Path, benchmark_path: Path,
                comparison_keys: Sequence[str]) -> None:
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
    """

    with h5py.File(result_path) as result, h5py.File(benchmark_path) as benchmark:
        for key in comparison_keys:
            if isinstance(key, (tuple, list)):
                key, subset = key
            else:
                subset = slice(None)
            np.testing.assert_array_almost_equal(result[key], benchmark[key][subset])
