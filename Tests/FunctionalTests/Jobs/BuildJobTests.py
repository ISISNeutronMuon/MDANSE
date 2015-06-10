from MDANSE import REGISTRY

for v in REGISTRY['job'].itervalues():
    v.save("Test_%s.py" % v.type)