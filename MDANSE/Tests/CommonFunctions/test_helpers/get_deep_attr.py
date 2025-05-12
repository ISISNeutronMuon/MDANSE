from typing import Any

def get_deep_attr(obj: Any, key: str) -> Any:
    """Get attribute from nested objects.

    Parameters
    ----------
    obj : Any
        Object to get elements from.
    key : str
        "." separated string indexing into object.

        "[x]" and "(x, y)" elements are evaluated.

    Returns
    -------
    Any
        Element at path given by key.
    """

    parts = key.split(".")

    new = obj
    for part in parts:
        part, *method = part.split("(", 1)
        part, *getter = part.split("[", 1)
        new = getattr(new, part)
        if method:
            args = method[0].strip("()")
            if args:
                args = args.split(",")

            new = new(*map(eval, args))
        if getter:
            args = getter[0].strip("[]")
            new = new[eval(args)]

    return new
