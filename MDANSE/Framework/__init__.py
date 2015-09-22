import os

from MDANSE import PLATFORM,PREFERENCES,REGISTRY

directories = sorted([x[0] for x in os.walk(os.path.dirname(__file__))][1:])

macrosDir = PREFERENCES['macros_directory'].get_value()
directories.insert(0,macrosDir)
directories.extend(sorted([x[0] for x in os.walk(macrosDir)][1:]))

for d in directories:
    REGISTRY.update_registry(d)
