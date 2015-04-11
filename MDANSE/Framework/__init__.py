import os

from MDANSE import REGISTRY

directories = sorted([x[0] for x in os.walk(os.path.dirname(__file__))][1:])

for d in directories:
    REGISTRY.update_registry(d)
