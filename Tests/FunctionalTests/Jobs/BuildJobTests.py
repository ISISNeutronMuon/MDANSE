from MDANSE import REGISTRY

for k,v in REGISTRY['job'].items():
    
    # Skip the mcstas test because mcstas executable is not available on all platform
    if k=='mvi':
        continue
    v.build_test("Test_%s.py" % v.type)
