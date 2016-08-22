import os

from MDANSE import PLATFORM,REGISTRY

directories = sorted([x[0] for x in os.walk(os.path.dirname(__file__))][1:])

macrosDir = PLATFORM.macros_directory()
directories.insert(0,macrosDir)
directories.extend(sorted([x[0] for x in os.walk(macrosDir)][1:]))

for d in directories:
    REGISTRY.update_registry(d)
