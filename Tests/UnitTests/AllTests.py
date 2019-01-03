import unittest
import os
import glob
import sys

def suite():
    files = glob.glob('Test*.py')
    modules = [__import__(os.path.splitext(f)[0],globals(),locals(),[],-1) for f in files]
    test_suite = unittest.TestSuite()
    for m in modules:
        test_suite.addTests(m.suite())

    return test_suite

def run_test():
    if not unittest.TextTestRunner(verbosity=2).run(suite()).wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    run_test()
