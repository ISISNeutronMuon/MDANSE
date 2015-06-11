from MDANSE import REGISTRY

for v in REGISTRY['job'].itervalues():
    v.build_test("Test_%s.py" % v.type)