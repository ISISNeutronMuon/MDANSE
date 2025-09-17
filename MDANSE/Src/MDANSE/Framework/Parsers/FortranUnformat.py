"""General parser for the Fortran Unformatted file format."""

from __future__ import annotations

from collections.abc import Generator
from os import SEEK_CUR
from typing import BinaryIO, Literal

FortranBinaryReader = Generator[bytes, int | bool, None]

STRUCT_CONV: dict[str, Literal["<", ">"]] = {
    "big": "<",
    "little": ">",
    "<": "<",
    ">": ">",
}
FROM_BYTES_CONV: dict[str, Literal["little", "big"]] = {
    "big": "big",
    "little": "little",
    "<": "little",
    ">": "big",
}


def binary_file_reader(
    file: BinaryIO, endian: Literal["big", "little", ">", "<"] = "big"
) -> FortranBinaryReader:
    """Yield the elements of a Fortran unformatted file.

    Parameters
    ----------
    file : BinaryIO
        Open file to get binary data from.
    endian : Literal["big", "little", "<", ">"]
        Endianness of data.

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
    endian = FROM_BYTES_CONV[endian]

    while bin_size := file.read(4):
        size = int.from_bytes(bin_size, endian)
        data = file.read(size)
        skip = yield data
        file.read(4)
        if skip:  # NB. Send proceeds to yield.
            # `True` implies rewind 1
            if skip < 0 or skip is True:
                for _ in range(abs(skip) - 1):
                    # Rewind to record size before last read
                    file.seek(-size - 12, SEEK_CUR)
                    size = int.from_bytes(file.read(4), endian)

                # Rewind one extra (which will be yielded)
                file.seek(-size - 8, SEEK_CUR)
            else:
                for _ in range(skip):
                    size = int.from_bytes(file.read(4), endian)
                    file.seek(size + 4, SEEK_CUR)
