"""General parser for the Fortran Unformatted file format."""
from collections.abc import Generator
from os import SEEK_CUR
from typing import BinaryIO

FortranBinaryReader = Generator[bytes, int, None]


def binary_file_reader(file: BinaryIO) -> FortranBinaryReader:
    """Yield the elements of a Fortran unformatted file.

    Parameters
    ----------
    file : BinaryIO
        Open file to get binary data from.

    Yields
    ------
    bytes
        Binary data record from Fortran file.

    Receives
    --------
    int | bool
        Skip/rewind amount (``True`` == ``-1``).

    Notes
    -----
    Each "record" is:

    ``(pre_nbytes: 4; data: nbytes; post_nbytes: 4)``

    Where ``pre_nbytes == post_nbytes`` (this is used in Fortran for rewinding).

    So when we rewind, we rewind the current size + ``post_nbytes``
    (current) + ``pre_nbytes`` (current) + ``post_nbytes`` (previous) [cursor
    now before post_nbytes (previous)] which is then read putting the
    cursor after post_nbytes (previous).

    When we do the final rewind, we put the cursor before ``pre_nbytes``
    ready to read the record.
    """
    while bin_size := file.read(4):
        size = int.from_bytes(bin_size, "big")
        data = file.read(size)
        skip = yield data
        file.read(4)
        if skip:  # NB. Send proceeds to yield.
            # `True` implies rewind 1
            if skip < 0 or skip is True:
                for _ in range(abs(skip) - 1):
                    # Rewind to record size before last read
                    file.seek(-size - 12, SEEK_CUR)
                    size = int.from_bytes(file.read(4), "big")

                # Rewind one extra (which will be yielded)
                file.seek(-size - 8, SEEK_CUR)
            else:
                for _ in range(skip):
                    size = int.from_bytes(file.read(4), "big")
                    file.seek(size + 4, SEEK_CUR)
