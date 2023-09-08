import glob
import os

# from .reader_registry import REGISTERED_READERS


def path_to_module(path, stop=""):
    path, _ = os.path.splitext(path)

    splitted_path = path.split(os.sep)

    try:
        idx = splitted_path[::-1].index(stop)
    except ValueError:
        idx = 0
    finally:
        module = ".".join(splitted_path[len(splitted_path) - 1 - idx :])

    return module


# # Import all classes in this directory so that classes with @register_reader are registered.
# pwd = os.path.dirname(__file__)
# for x in glob.glob(os.path.join(pwd, '*.py')):
#     mod, _ = os.path.splitext(x)
#     mod = os.path.basename(mod)
#     if mod.startswith('__'):
#         continue

#     module = path_to_module(x, stop="waterstay")
#     __import__(module, globals(), locals())

# __all__ = ['REGISTERED_READERS']
