from MDANSE.Chemistry import ATOMS_DATABASE


def guess_element(atm_label: str) -> str:
    """From an input atom label find a match to an element in the atom
    database.

    Parameters
    ----------
    atm_label : str
        The atom label.

    Returns
    -------
    str
        The symbol of the guessed element.

    Raises
    ------
    AttributeError
        Error if unable to match to an element.
    """
    guess = "".join([i for i in atm_label if i.isalpha()])
    if guess in ATOMS_DATABASE:
        return guess
    raise AttributeError(f"Unable to guess: {atm_label}")


def get_element_from_mapping(
    grp_label: str, atm_label: str, mapping: dict[str, dict[str, str]]
) -> str:
    """Get the symbol of the element from group and atom labels.

    Parameters
    ----------
    grp_label : str
        The atom grouping label.
    atm_label : str
        The atom label.
    mapping : dict[str, dict[str, str]]
        A dict which maps group and atom labels to an element from the
        atom database.

    Returns
    -------
    str
        The symbol of the element from the MDANSE atom database.
    """
    if grp_label in mapping and atm_label in mapping[grp_label]:
        element = mapping[grp_label][atm_label]
    else:
        element = guess_element(atm_label)
    return element


def fill_remaining_labels(
    labels: list[tuple[str, str]], mapping: dict[str, dict[str, str]]
) -> None:
    """Given a list of labels fill the remaining labels in the mapping
    dictionary.

    Parameters
    ----------
    labels : list[tuple[str, str]]
        A list of group and atom labels.
    mapping : dict[str, dict[str, str]]
        The atom mapping dictionary.
    """
    for grp_label, atm_label in labels:
        if grp_label not in mapping:
            mapping[grp_label] = {}
        if atm_label not in mapping[grp_label]:
            mapping[grp_label][atm_label] = guess_element(atm_label)


def check_mapping_valid(
    labels: list[tuple[str, str]], mapping: dict[str, dict[str, str]]
):
    """Given a list of labels check that the mapping is valid.

    Parameters
    ----------
    labels : list[tuple[str, str]]
        A list of group and atom labels.
    mapping : dict[str, dict[str, str]]
        The atom mapping dictionary.

    Returns
    -------
    bool
        True if the mapping is valid.
    """
    for grp_label, atm_label in labels:
        if grp_label not in mapping or atm_label not in mapping[grp_label]:
            return False
        if mapping[grp_label][atm_label] not in ATOMS_DATABASE:
            return False
    return True
