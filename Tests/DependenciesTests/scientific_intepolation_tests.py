#
# Tests for Scientific.Functions.Interpolation
#
# Written by Konrad Hinsen <hinsen@cnrs-orleans.fr>
# last revision: 2011-2-18
#

import unittest
import copy
from Scientific.Functions.Interpolation import InterpolatingFunction as IF
from Scientific import N

class InterpolatingFunctionTest(unittest.TestCase):

    def testRetrieval(self):
        x = N.arange(0., 1., 0.1)
        y = N.arange(0., 2., 0.1)
        v = x[:, N.NewAxis]*y[N.NewAxis, :]
        f = IF((x, y), v)
        for ix, xp in enumerate(x):
            for iy, yp in enumerate(y):
                self.assertEqual(f(xp, yp), v[ix, iy])
    
    def testAxes(self):
        x = N.arange(0., 1., 0.1)
        y = N.arange(0., 2., 0.1)
        v = x[:, N.NewAxis]*y[N.NewAxis, :]
        self.assertRaises(ValueError,
                          lambda: IF((x[:-2], y), v))
        self.assertRaises(ValueError,
                          lambda: IF((x, y[1:]), v))
        self.assertRaises(ValueError,
                          lambda: IF((x[:, N.NewAxis], y), v))
        self.assertRaises(ValueError,
                          lambda: IF((x, y[::-1]), v))
        self.assertRaises(ValueError,
                          lambda: IF((x, 0*y), v))
        

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(InterpolatingFunctionTest))
    return s

if __name__ == '__main__':
    unittest.main()
