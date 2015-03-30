from MDANSE import REGISTRY

for v in REGISTRY['job'].itervalues():
    v.save("Test%s.py" % v.type.upper())