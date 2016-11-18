import os

from MDANSE import PLATFORM, REGISTRY

REGISTRY.update(os.path.join(os.path.dirname(__file__),"*"))

macrosDirectories = sorted([x[0] for x in os.walk(PLATFORM.macros_directory())][0:])
for d in macrosDirectories:
    REGISTRY.update(d)
