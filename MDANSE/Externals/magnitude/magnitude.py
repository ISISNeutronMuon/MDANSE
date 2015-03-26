# magnitude  -- a module for computing with numbers with units.
#
# Version 0.9.4, November 2009
#
# Copyright (C) 2006-2009 Juan Reyero (http://juanreyero.com).
# 
# Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.  See the License for the specific
# language governing permissions and limitations under the
# License.
# 
# Home page: http://juanreyero.com/magnitude/

"""
A physical quantity is a number with a unit, like 10 km/h. Units can be any
of the SI units, plus a bunch of non-SI, bits, dollars, and any combination
of them. They can include the standard SI prefixes. Magnitude can operate
with physical quantities, parse their units, and print them. You don't have
to worry about unit consistency or conversions; everything is handled
transparently. By default output is done in basic SI units, but you can
specify any output unit, as long as it can be reduced to the basic units of
the physical quantity.

The basic units understood by the magnitude module are:

    indicator    meaning
    ---------    -------
    $            dollar ('dollar' is also acceptable)
    A            ampere
    b            bit
    cd           candela
    K            degrees Kelvin
    kg           kilograms
    m            meters
    mol          amount of substance
    s            seconds

From these basic units you can derive many other units.  The magnitude
package predefines these derived units:

    Bq           becquerel
    C            coulomb
    c            speed of light (m/s)
    day
    degC         degree Celsius
    dpi          dots per inch
    F            farad
    ft           feet ("'" is also acceptable)
    g            gram
    gravity      acceleration due to gravity (m/s**2)
    Gy           gray
    H            henry
    h            hour
    Hz           Hertz
    inch         ('"' is also acceptable)
    ips          inches per second
    J            joule
    kat          katal
    l            liter
    lightyear    light year
    lm           lumen
    lpi          lines per inch
    lux
    min          minute
    N            newton
    ohm
    Pa           pascal
    S            siemens
    Sv           sievert
    T            tesla
    V            volt
    W            watt
    Wb           weber
    year
    B            byte

Two magnitudes have no units, 'rad' (radian - unit of plane angle) and 'sr'
(steradian - unit of solid angle).

Any of the above units can be augmented with the following set of scale
prefixes:

    letter     scale    name
    ------     -----    ----
    y          1e-24    yocto
    z          1e-21    zepto
    a          1e-18    atto
    f          1e-15    femto
    p          1e-12    pico
    n          1e-9     nano
    u          1e-6     micro
    m          1e-3     mili
    c          1e-2     centi
    d          1e-1     deci
    k          1e3      kilo
    Ki         2^10     Kibi
    M          1e6      mega
    Mi         2^20     Mebi
    G          1e9      giga
    Gi         2^30     Gibi
    T          1e12     tera
    Ti         2^40     Tebi
    P          1e15     peta
    Pi         2^50     Pebi
    E          1e18     exa
    Ei         2^60     Exbi
    Z          1e21     zetta
    Y          1e24     yotta

Exported symbols
----------------

- Magnitude [class] --- Numbers with units; math operations are overloaded
- mg(number, unit, ounit='') --- Construct a Magnitude
- ensmg(m, unit='') --- Tries to build a Magnitude out of something
- newmag(indicator, mag) --- Intern a new magnitude with its name
- MagnitudeError [class] --- Magnitude error handling


Defining new magnitudes
-----------------------

You can define new magnitudes by instantiating the Magnitude class.  Suppose
you want to define pounds as a magnitude and associate with it the unit
'lb'.  A pound is 0.45359237 kilograms, so we have

    >>> lb = Magnitude(0.45359237, kg=1)

To make it recognized automatically you also have to introduce it to
the system:

    >>> new_mag('lb', lb)

You can then use it as you would any other predefined physical quantity:

    >>> me = mg(180, 'lb')
    >>> print me.ounit('kg').toval()
    81.6466266

The following online references provide more detail about physical units and
the SI system.

    http://physics.nist.gov/cuu/Units/units.html
    http://en.wikipedia.org/wiki/SI
    http://www.gnu.org/software/units/units.html for units.dat
    http://www.cip.physik.uni-muenchen.de/~tf/misc/etools.lisp

This code was very much inspired by
    http://www.cs.utexas.edu/users/novak/units.html
and its associated paper,
    http://www.cs.utexas.edu/users/novak/units95.html


Bits and bytes (2009-11-03)
---------------------------

A previous version of the library used "bit" for bit and "b" for byte,
leaving B for Bel.  Following Michael Scheper's suggestion we follow
now IEEE 1541 and use "b" for bit and "B" for byte.  If the need
arises I'll implement ad-hoc esupport for dB, but for the time being
there is none.
"""

import re, math
import types

# Base magnitude names and prefixes.  The MAGS dictionary, initialized
# at the end, will contain all the known magnitudes.  Units are
# 9-element arrays, each element the exponent of the unit named by the
# Uname in the same position. 

class MagnitudeError(Exception):
    pass

MAGS = {}
_unames = ['m', 's', 'K', 'kg', 'A', 'mol', 'cd', '$', 'b']
_prefix = {'y': 1e-24,  # yocto
           'z': 1e-21,  # zepto
           'a': 1e-18,  # atto
           'f': 1e-15,  # femto
           'p': 1e-12,  # pico
           'n': 1e-9,   # nano
           'u': 1e-6,   # micro
           'm': 1e-3,   # mili
           'c': 1e-2,   # centi
           'd': 1e-1,   # deci
           'da': 1e1,    # deka
           'h': 1e2,    # hecto
           'k': 1e3,   # kilo
           'M': 1e6,    # mega
           'G': 1e9,    # giga
           'T': 1e12,   # tera
           'P': 1e15,   # peta
           'E': 1e18,   # exa
           'Z': 1e21,   # zetta
           'Y': 1e24,   # yotta

           # Binary prefixes, approved by the International
           # Electrotechnical Comission in 1998.  Since then, kb means
           # 1000 bytes; for 1024 bytes use Kib (note the capital K in
           # the binary version, and the lower case for the b of byte,
           # see comment in byte definition below).
           'Ki': 2 ** 10, # Kibi (<- kilo, 10^3)
           'Mi': 2 ** 20, # Mebi (<- mega, 10^6)
           'Gi': 2 ** 30, # Gibi (<- giga, 10^9)
           'Ti': 2 ** 40, # Tebi (<- tera, 10^12)
           'Pi': 2 ** 50, # Pebi (<- peta, 10^15)
           'Ei': 2 ** 60  # Exbi (<- exa, 10^18)
           }


###### Default print formatting options

_default_prn_format = "%.*f"
_prn_format = _default_prn_format
_prn_prec = 4
_prn_units = True

def reset_default_format():
    """Resets the default output format.

    By default the output format is "%.*f", where * gets replaced by
    the output precision.
    """
    global _prn_format
    _prn_format = _default_prn_format
    
def default_format(fmt=None):
    """Get or set the default ouptut format.  

    Include a fmt if and where you need to specify the output
    precision.  Defaults to %.*f, where the * stands for the
    precision.  Do nothing if fmt is None. 

    Returns: default format.

    >>> print mg(2, 'm2').sqrt()
    1.4142 m
    >>> default_format("%.2f")
    '%.2f'
    >>> print mg(2, 'm2').sqrt()
    1.41 m
    >>> reset_default_format()
    """
    global _prn_format
    if fmt is not None:
        _prn_format = fmt
    return _prn_format

def output_precision(prec=None):
    """Get or set the output precision.  

    Package default is 4.  Do nothing is prec is None. 

    Returns: default precision. 

    >>> default_format("%.*f")
    '%.*f'
    >>> print mg(2, 'm2').sqrt()
    1.4142 m
    >>> output_precision(6)
    6
    >>> print mg(2, 'm2').sqrt()
    1.414214 m
    >>> output_precision(4)
    4
    """
    global _prn_prec
    if prec is not None:
        _prn_prec = prec
    return _prn_prec

def output_units(un=None):
    """Enable or disable the output of units when printing. 

    By default output of units is enabled.  Do nothing if un is None.
    When disabled (un is False) print of Magnitudes will produce only
    numbers.

    Return: True if output of units enabled, False otherwise. 

    >>> print mg(2, 'day')
    2.0000 day
    >>> output_units(False)
    False
    >>> print mg(2, 'day').ounit('s')
    172800.0000
    """
    global _prn_units
    if un is not None:
        _prn_units = un
    return _prn_units


###### Resolution areas

def _res2num(res):
    match = re.search(r'(\d+)x(\d+)', res)
    if match:
        return int(match.group(1)), int(match.group(2))
    if (res[0] == '[') and (res[-1] == ']'):
        return (int(res[1:-1]), int(res[1:-1]))

def _isres(res):
    return (len(res) > 2) and (res[0] == '[') and (res[-1] == ']')

def _res2m2(res):
    """Convert resolution string to square meters. 

    Bracketed resolutions are used in the printing industry, to
    denote the area of a pixel.  Can be like [300x1200] or like [600]
    (=[600x600]), meaning the area of square pixels of size 1"/300 x
    1"/1200 and 1"/600 x 1"/600.  The square brackes are intended to
    show that we are talking about areas.  This function converts them
    to square meters.

    >>> _res2m2("[600x600]")
    1.7921111111111111e-09
    >>> _res2m2("[600]")
    1.7921111111111111e-09
    >>> _res2m2("[150x300]")
    1.4336888888888889e-08
    """
    hr, vr = _res2num(res)
    return 0.0254 * 0.0254 / (vr * hr)


# Definition of the magnitude type.  Includes operator overloads.

def _numberp(n):  ## Python has to have a decent way to do this!
    return (isinstance(n, types.ComplexType) or
            isinstance(n, types.FloatType) or
            isinstance(n, types.IntType) or
            isinstance(n, types.LongType))

class Magnitude:
    def __init__(self, val, m=0, s=0, K=0, kg=0, A=0, mol=0, cd=0, dollar=0, b=0):
        self.val = val
        self.unit = [m, s, K, kg, A, mol, cd, dollar, b]
        self.out_unit = None
        self.out_factor = None
        self.oprec = None
        self.oformat = None

    def copy(self, with_format=False):
        """Builds and returns a copy of a magnitude. 

        The copy includes value and units.  If with_format is set to
        True the default output unit, output factor, output precision
        and output format are also copied. 

        >>> a = mg(1000/3., 'mm')
        >>> a.output_prec(2)
        >>> print a
        333.33 mm
        >>> print a.copy()
        0.3333 m
        >>> print a.copy(with_format=True)
        333.33 mm
        """
        cp = Magnitude(self.val, *self.unit)
        if with_format:
            cp.out_unit = self.out_unit
            cp.out_factor = self.out_factor
            cp.oprec = self.oprec
            cp.oformat = self.oformat
        return cp

    def toval(self, ounit=''):
        """Returns the numeric value of a magnitude.

        The value is given in ounit or in the Magnitude's default
        output unit.

        >>> v = mg(100, 'km/h')
        >>> v.toval()
        100.0
        >>> v.toval(ounit='m/s')
        27.777777777777779
        """
        m = self.copy()
        if not ounit:
            ounit = self.out_unit
        if ounit:
            out_factor = self.sunit2mag(ounit)
            m._div_by(out_factor)
        return m.val

    def __str__(self):
        oformat = self.oformat
        oprec = self.oprec
        if oprec is None:
            oprec = _prn_prec
        if oformat is None:
            oformat = _prn_format
        if self.out_unit:
            m = self.copy()
            m._div_by(self.out_factor)
            if '*' in oformat:  # requires the precision arg
                st = oformat % (oprec, m.val)
            else:
                st = oformat % (m.val)
            if _prn_units:
                return st + ' ' + self.out_unit.strip()
            return st

        if '*' in oformat:
            st = oformat % (oprec, self.val)
        else:
            st = oformat % (self.val)
            
        if not _prn_units:
            return st

        u = self.unit
        num = ' '  # numerator
        for i in range(len(_unames)):
            if u[i] == 1:
                num = num + _unames[i] + ' '
            elif u[i] > 0:
                num = num + _unames[i] + str(u[i]) + ' '
        den = ''  # denominator
        for i in range(len(_unames)):
            if u[i] == -1:
                den = den + _unames[i] + ' '
            elif u[i] < 0:
                den = den + _unames[i] + str(-u[i]) + ' '
        if den:
            if num == ' ':
                num += '1 '
            st += (num + '/ ' + den)
        elif num != ' ':
            st += num        
        return st.strip()

    def term2mag(self, s):
        """Converts a string with units to a Magnitude.  

        Can't divide: use with the numerator and the denominator
        separately (hence the "term").  Returns the Magnitude that the
        string represents.  Units are separated by spaces, powers are
        integers following the unit name.

        Cannot parse fractional units.  Cannot parse multi-digit
        exponents.

        >>> a = mg(1, '')
        >>> print a.term2mag('V2  A')
        1.0000 m4 kg2 / s6 A
        >>> print a.term2mag('kft year') # kilo-feet year
        9618551037.0820 m s
        """
        m = Magnitude(1.0)
        units = re.split(r'\s', s)
        for u in units:
            if re.search(r'[^\s]', u):
                exp = 1
                if re.search(r'\d$', u):
                    exp = int(u[-1])
                    u = u[0:-1]
                if MAGS.has_key(u):
                    u = MAGS[u].copy()
                elif ((len(u)>=3) and _prefix.has_key(u[0:2]) and
                      MAGS.has_key(u[2:])):
                    pr = _prefix[u[0:2]]
                    u = MAGS[u[2:]].copy();  u.val = pr * u.val
                elif ((len(u)>=2) and _prefix.has_key(u[0]) and
                      MAGS.has_key(u[1:])):
                    pr = _prefix[u[0]]
                    u = MAGS[u[1:]].copy();  u.val = pr * u.val
                elif _isres(u):
                    u = Magnitude(_res2m2(u), m=2)
                elif u == '':
                    u = Magnitude(1.0)
                else:
                    raise MagnitudeError("Don't know about unit %s" % u)
                for i in range(exp):
                    m._mult_by(u)
        return m

    def sunit2mag(self, unit=''):
        """Convert a units string to a Magnitude. 

        Uses term2mag to convert a string with units, possibly
        including a / to separate a numerator and a denominator, to a
        Magnitude.

        >>> a = mg(1, '')
        >>> a.sunit2mag('m/s').toval()
        1.0
        >>> a.sunit2mag('km/h').toval()
        0.27777777777777779
        >>> print a.sunit2mag('W h')
        3600.0000 m2 kg / s2
        >>> print a.sunit2mag('W h').ounit('J')
        3600.0000 J
        >>> print a.sunit2mag('m2 kg / s3 Pa')
        1.0000 m3 / s
        >>> print a.sunit2mag('m2 kg/s3').ounit('W')
        1.0000 W
        """
        m = Magnitude(1.0)
        if unit:
            q = re.split(r'/', unit)
            if re.search(r'[^\s]', q[0]):
                m._mult_by(self.term2mag(q[0]))
            if (len(q) == 2) and re.search(r'[^\s]', q[1]):
                m._div_by(self.term2mag(q[1]))
        return m

    def dimensionless(self):
        """True if the magnitude's dimension exponents are all zero. 

        >>> mg(2, 'K').dimensionless()
        False
        >>> mg(2, 'rad').dimensionless()
        True
        """
        return self.unit == [0] * 9

    def dimension(self):
        """Return the dimension of the unit in internal (array) format. 

        >>> mg(2, 'J').dimension()
        [2, -2, 0, 1, 0, 0, 0, 0, 0]
        """
        return self.unit[:]
    
    def has_dimension(self, u):
        """Returns true if the dimension of the magnitude matches u:

        >>> s = mg(120, 'km/h') * (2, 'day')
        >>> s.has_dimension('m')
        True
        >>> print s.ounit('cm')
        576000000.0000 cm
        """
        o = self.sunit2mag(u)
        return (self.unit == o.unit)

    def _mult_by(self, m):
        self.val *= m.val
        for i in range(len(self.unit)):
            self.unit[i] = self.unit[i] + m.unit[i]
        self.out_unit = None

    def _div_by(self, m):
        self.val /= m.val
        for i in range(len(self.unit)):
            self.unit[i] = self.unit[i] - m.unit[i]
        self.out_unit = None

    def ounit(self, unit):
        """Set the preferred unit for output, returning the Magnitude.

        >>> a = mg(1, 'kg m2 / s2')
        >>> print a
        1.0000 kg m2 / s2
        >>> print a.ounit('J')
        1.0000 J
        >>> print a
        1.0000 J
        """
        self.out_unit = unit
        self.out_factor = self.sunit2mag(unit)
        if self.out_factor.unit != self.unit:
            raise MagnitudeError("Inconsistent Magnitude units: %s, %s" % 
                                (self.out_factor.unit, self.unit))
        return self

    def output_prec(self, prec):
        """Set the output precision for the Magnitude.

        If not set, the the module's default will be used, set and
        queried with output_precision(prec).

        >>> a = mg(5, 'm3') ** (1/3.)  # Careful with precedence of **
        >>> print a
        1.7100 m
        >>> a.output_prec(1)
        >>> print a
        1.7 m
        """
        self.oprec = prec

    def output_format(self, oformat):
        """Set the output format for the Magnitude. 

        If not set, the module's default will be used, set and queried
        with default_format(fmt).  Default value is "%.*f".  The star
        will be replaced by the expected output precision.

        >>> a = mg(5, 'm2').sqrt()
        >>> print a
        2.2361 m
        >>> a.output_format("%03d")
        >>> print a
        002 m
        """
        self.oformat = oformat

    def __coerce__(self, m):
        """Force tuples or numbers into Magnitude."""

        if not isinstance(m, Magnitude):
            if type(m) == tuple:
                if len(m) == 2:
                    r = Magnitude(m[0])
                    r._mult_by(self.sunit2mag(m[1]))
                    return self, r
                elif len(m) == 1:
                    return self, Magnitude(m[0])
                else:
                    return None
            elif _numberp(m):
                return self, Magnitude(m)
            else:
                return None
        else:
            return self, m

    def __add__(self, m):
        """Add Magnitude instances.

        >>> print mg(10, 'm') + (20, 'km') + (30, 'lightyear')
        283821914177444000.0000 m
        """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        r = self.copy()
        r.val += m.val
        return r

    def __radd__(self, m):
        """Add Magnitude instances.  See __add__. """
        return self.__add__(m)

    def __iadd__(self, m):
        """Add Magnitude instances.  See __add__. """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        self.val += m.val
        return self
    
    def __sub__(self, m):
        """Substract Magnitude instances. 

        >>> print mg(20, 'm/s') - (1, 'km/h')
        19.7222 m / s
        """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        r = self.copy()
        r.val -= m.val
        return r

    def __rsub__(self, m):
        """Substract Magnitude instances.  See __sub__."""
        return m.__sub__(self)

    def __isub__(self, m):
        """Substract Magnitude instances.  See __sub__."""
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        self.val -= m.val
        return self

    def __mul__(self, m):
        """Multiply Magnitude instances.

        >>> print mg(10, 'm/s') * (10, 's')
        100.0000 m
        """
        r = self.copy()
        r._mult_by(m)
        return r

    def __rmul__(self, m):
        """Multiply Magnitude instances.  See __mul__."""
        r = self.copy()
        r._mult_by(m)
        return r

    def __imul__(self, m):
        """Multiply Magnitude instances.  See __mul__."""
        self._mult_by(m)
        return self

    def __div__(self, m):
        """Divide Magnitude instances.

        >>> print mg(100, 'V') / (10, 'kohm')
        0.0100 A
        """
        r = self.copy()
        r._div_by(m)
        return r

    def __rdiv__(self, m):
        """Divide Magnitude instances.  See __div__."""
        r = self.copy()
        m._div_by(r)
        return m

    def __idiv__(self, m):
        """Divide Magnitude instances.  See __div__."""
        self._div_by(m)
        return self

    def __mod__(self, n):
        """Modulus of a Magnitude by a number or a Magnitude.

        Unit is that of the left hand side operator. 

        >>> print mg(10, 'm/s') % 3
        1.0000 m / s
        >>> print mg(10, 'm/s') % (3, 'W')
        1.0000 m / s
        """
        r = self.copy()
        r.val = r.val % ensmg(n).toval()
        return r

    def __imod__(self, n):
        """Modulus of a Magnitude by a number or a Magnitude.  See __mod__."""
        self.val %= n.val
        for i in range(len(self.unit)):
            self.unit[i] = self.unit[i] - n.unit[i]
        self.out_unit = None
        return self

    def __floordiv__(self, m):
        """Floordiv of two Magnitude instances. 

        >>> print mg(10, 'm/s') // (3, 's')
        3.0000 m / s2
        >>> print mg(-10, 'm/s') // (3, 'm')
        -4.0000 1 / s
        """
        r = self.copy()
        r._div_by(m)
        r.val = math.floor(r.val)
        return r

    def __ifloordiv__(self, m):
        """Floordiv of two Magnitude instances. See __floordiv__."""
        self._div_by(m)
        self.val = math.floor(self.val)
        return self
        
    def __divmod__(self, m):
        """Floordiv and remainder of two Magnitude instances. 

        >>> [ str(i) for i in divmod(mg(10, 'm/s'), (3, 's')) ]
        ['3.0000 m / s2', '1.0000 m / s']
        """
        return (self.__floordiv__(m), self.__mod__(m))

    def __rdivmod__(self, m):
        """Floordiv and remainder of two Magnitude instances. See __divmod___"""
        return (m.__floordiv__(self), m.__mod__(self))

    def __pow__(self, n, modulo=None):
        """Return a Magnitude to the power n.  

        If modulo is present return the result modulo it.

        >>> print mg(10, 'm/s') ** 2
        100.0000 m2 / s2
        >>> print pow(mg(10, 'km/h'), mg(2)) # Exponent cannot have dimension
        7.7160 m2 / s2
        >>> print pow(mg(10, 'm/s'), 2, 3)
        1.0000 m2 / s2
        """
        r = self.copy()
        if modulo and (r.val == math.floor(r.val)):  # it's an integer
            # might have been converted to float during creation,
            # modulo only works when all are int
            r.val = int(r.val)
        if isinstance(n, Magnitude):  # happens when called as a ** n
            if not n.dimensionless():
                raise MagnitudeError("Cannot use a dimensional number as"
                                     "exponent, %s" % (n))
            n = n.val
        r.val = pow(r.val, n, modulo)
        for i in range(len(r.unit)):
            r.unit[i] *= n
        return r

    def __ipow__(self, n):
        """Power of a Magnitude.  See __pow___."""
        if not n.dimensionless():
            raise MagnitudeError("Cannot use a dimensional number as"
                                 "exponent, %s" % (n))
        n = n.val
        self.val = pow(self.val, n)
        for i in range(len(self.unit)):
            self.unit[i] *= n
        return self

    def __neg__(self):
        """Multiply by -1 the value of the Magnitude."""
        r = self.copy()
        r.val = -r.val
        return r

    def __pos__(self):
        """Unary plus operator. """
        return self.copy()

    def __abs__(self):
        """Absolute value of a Magnitude. 

        >>> print abs(mg(-10, 'm'))
        10.0000 m
        """
        r = self.copy()
        r.val = abs(r.val)
        return r

    def __cmp__(self, m):
        """Compare two Magnitude instances with the same dimensions.

        >>> print mg(10, 'm/s') > (11, 'km/h')
        True
        >>> print mg(1, 'km') == (1000, 'm')
        True
        """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units in comparison: %s and %s" %
                                 (m.unit, self.unit))
        return cmp(self.val, m.val)

    def __int__(self):
        """Return the value of a Magnitude coerced to integer.

        Note that this will happen to the value in the default output unit:

        >>> print int(mg(10.5, 'm/s'))
        10
        >>> print int(mg(10.5, 'm/s').ounit('km/h'))
        37
        """
        return int(self.toval())

    def __long__(self):
        """Return the value of a Magnitude coerced to long.  See __int__."""
        return long(self.toval())

    def __float__(self):
        """Return the value of a Magnitude coerced to float.  See __int__."""
        return float(self.toval())

    def ceiling(self):
        """Ceiling of a Magnitude's value in canonical units.

        >>> print mg(10.2, 'm/s').ceiling()
        11.0000 m / s
        >>> print mg(3.6, 'm/s').ounit('km/h').ceiling()
        4.0000 m / s
        >>> print mg(50.3, 'km/h').ceiling()
        14.0000 m / s
        """
        r = self.copy(with_format=False)
        r.val = math.ceil(r.val)
        return r

    def floor(self):
        """Floor of a Magnitude's value in canonical units. 

        >>> print mg(10.2, 'm/s').floor()
        10.0000 m / s
        >>> print mg(3.6, 'm/s').ounit('km/h').floor()
        3.0000 m / s
        >>> print mg(50.3, 'km/h').floor()
        13.0000 m / s
        """
        r = self.copy()
        r.val = math.floor(r.val)
        return r

    def round(self):
        """Round a Magnitude's value in canonical units. 

        >>> print mg(10.2, 'm/s').round()
        10.0000 m / s
        >>> print mg(3.6, 'm/s').ounit('km/h').round()
        4.0000 m / s
        >>> print mg(50.3, 'km/h').round()
        14.0000 m / s
        """
        r = self.copy()
        r.val = round(r.val)
        return r

    def to_bits(self):
        return Magnitude(math.ceil(math.log(self.val) / math.log(2.0)),
                         b=1)

    def sqrt(self):
        """Square root of a magnitude. 

        >>> print mg(4, 'm2/s2').sqrt()
        2.0000 m / s
        >>> print mg(2, 'm/s').sqrt()
        1.4142 m0.5 / s0.5
        """
        return self ** 0.5
    
    
    def get_compatible_units(self):
        
        units = [k for k,v in MAGS.items() if v.unit == self.unit]
        
        return units
        
    
# Some helper functions

def mg(v, unit='', ounit=''):
    """Builds a Magnitude from a number and a units string:

    >>> print mg(10, 'm/s')
    10.0000 m/s
    >>> a = mg(10, 'm/s', 'km/h')
    >>> print a
    36.0000 km/h
    >>> a = mg(1, 'B')
    >>> print a
    1.0000 B
    >>> print a.ounit('b')
    8.0000 b
    >>> a = mg(1024, 'B')
    >>> print a.ounit('b')
    8192.0000 b
    >>> print a.ounit('KiB')
    1.0000 KiB
    """
    m = Magnitude(v)
    if unit:
        u = m.sunit2mag(unit)
        m._mult_by(u)
    if not ounit:
        ounit = unit
    m.ounit(ounit)
    return m

def ensmg(m, unit=''):
    """Converts something to a Magnitude.

    >>> print ensmg(10, 'Hz')
    10.0000 Hz
    >>> a = (4, 'mol')
    >>> print ensmg(a)
    4.0000 mol
    >>> a = mg(1024, 'Pa')
    >>> print ensmg(a)
    1024.0000 Pa
    >>> f = ensmg((10, 'Pa')) * (10, 'm2')
    >>> print f.ounit('N')
    100.0000 N
    """
    if not isinstance(m, Magnitude):
        if type(m) == tuple:
            if len(m) == 2:
                return mg(m[0], m[1], unit)
            elif (len(m) == 1) and _numberp(m[0]):
                if unit:
                    return mg(m[0], unit)
                return Magnitude(m[0])
            else:
                raise MagnitudeError("Can't convert %s to Magnitude" % (m,))
        elif _numberp(m):
            if unit:
                return mg(m, unit)
            return Magnitude(m)
        
        elif isinstance(m, basestring):
            
            if not m:
                raise MagnitudeError("Can't convert %r to Magnitude" % (m,))
                                        
            try:
                temp = m.split()
                val = temp[0].strip()
                try:
                    val = int(val)
                except ValueError:
                    try:
                        val = float(val)
                    except ValueError:
                        val = complex(val)
                unit = "".join(temp[1:]).replace(" ","")
            except ValueError:
                raise MagnitudeError("Can't convert %s to Magnitude" % (m,))
            else:
                return mg(val,unit)
                
        else:
            raise MagnitudeError("Can't convert %s to Magnitude" %
                                 (m,))
    else:
        return m

# These don't really help much, as it's much easier to use the
# overriden * and / operators.

def __mul(m1, *rest):
    m = ensmg(m1)
    for m2 in rest:  m._mult_by(ensmg(m2))
    return m

def __div(m1, *rest):
    if rest:
        m = ensmg(m1)
        for m2 in rest:  m._div_by(ensmg(m2))
        return m
    else:
        m = Magnitude(1.0)
        m._div_by(ensmg(m1))
        return m

def new_mag(indicator, mag):
    """Define a new magnitude understood by the package.

    Defines a new magnitude type by giving it a name (indicator) and
    its equivalence in the form of an already understood magnitude.

    >>> new_mag('mile', mg(160934.4, 'cm'))
    >>> print mg(100, 'mile/h').ounit('km/h')
    160.9344 km/h
    """

    MAGS[indicator] = mag

# Finally, define the Magnitudes and initialize MAGS.

def _init_mags():
    # Magnitudes for the base SI units
    new_mag('m', Magnitude(1.0, m=1))
    new_mag('s', Magnitude(1.0, s=1))
    new_mag('K', Magnitude(1.0, K=1))
    new_mag('kg', Magnitude(1.0, kg=1))
    new_mag('A', Magnitude(1.0, A=1))
    new_mag('mol', Magnitude(1.0, mol=1))
    new_mag('cd', Magnitude(1.0, cd=1))
    new_mag('$', Magnitude(1.0, dollar=1))
    new_mag('dollar', Magnitude(1.0, dollar=1))
    new_mag('b', Magnitude(1.0, b=1))           # bit

    # Magnitudes for derived SI units
    new_mag('B', Magnitude(8.0, b=1))
    new_mag('rad', Magnitude(1.0))  # radian
    new_mag('sr', Magnitude(1.0))  # steradian
    new_mag('Hz', Magnitude(1.0, s=-1))  # hertz
    new_mag('g', Magnitude(1e-3, kg=1))  # gram
    new_mag('N', Magnitude(1.0, m=1, kg=1, s=-2))  # newton
    new_mag('Pa', Magnitude(1.0, m=-1, kg=1, s=-2))  # pascal    
    new_mag('J', Magnitude(1.0, m=2, kg=1, s=-2))  # joule
    new_mag('W', Magnitude(1.0, m=2, kg=1, s=-3))  # watt
    new_mag('C', Magnitude(1.0, s=1, A=1))  # coulomb
    new_mag('V', Magnitude(1.0, m=2, kg=1, s=-3, A=-1))  # volt
    new_mag('F', Magnitude(1.0, m=-2, kg=-1, s=4, A=2))  # farad, C/V
    new_mag('ohm', Magnitude(1.0, m=2, kg=1, s=-3, A=-2))  # ohm, V/A
    new_mag('S', Magnitude(1.0, m=-2, kg=-1, s=3, A=2))  # siemens, A/V, el cond
    new_mag('Wb', Magnitude(1.0, m=2, kg=1, s=-2, A=-1))  # weber, V.s, mag flux
    new_mag('T', Magnitude(1.0, kg=1, s=-2, A=-1))  # tesla, Wb/m2, mg flux dens
    new_mag('H', Magnitude(1.0, m=2, kg=1, s=-2, A=-2))  # henry, Wb/A, induct.
    new_mag('degC', Magnitude(1.0, K=1))  # celsius, !!
    new_mag('lm', Magnitude(1.0, cd=1))  # lumen, cd.sr (=cd)), luminous flux
    new_mag('lux', Magnitude(1.0, m=-2, cd=1))  # lux, lm/m2, illuminance
    new_mag('Bq', Magnitude(1.0, s=-1))  # becquerel, activity of a radionulide
    new_mag('Gy', Magnitude(1.0, m=2, s=-2))  # gray, J/kg, absorbed dose
    new_mag('Sv', Magnitude(1.0, m=2, s=-2))  # sievert, J/kg, dose equivalent
    new_mag('kat', Magnitude(1.0, s=-1, mol=1))  # katal, catalitic activity
    
    ### Other
    # length
    new_mag("'", Magnitude(0.3048, m=1))  # feet
    new_mag('ft', Magnitude(0.3048, m=1))  # feet
    new_mag('inch', Magnitude(0.0254, m=1))  # inch
    new_mag('"', Magnitude(0.0254, m=1))  # inch
    new_mag('lightyear', Magnitude(2.99792458e8 * 365.25 * 86400, m=1))

    # surface
    new_mag('b', Magnitude(1.0e-28, m=2))

    # volume
    new_mag('l', Magnitude(0.001, m=3))

    # time
    # year is tropical year, "the mean interval between vernal
    # equinoxes.  Differs from the sidereal year by 1 part in 26000
    # due to precession of the earth about its rotational axis
    # combined with precession of the perihelion of the earth's orbit"
    # (from units.dat).
    new_mag('year', Magnitude(31556925.974678401, s=1)) 
    new_mag('day', Magnitude(86400, s=1))
    new_mag('h', Magnitude(3600, s=1))
    new_mag('min', Magnitude(60, s=1))

    # Resolution
    new_mag('dpi', Magnitude(1.0 / 0.0254, m=-1))
    new_mag('lpi', Magnitude(1.0 / 0.0254, m=-1))

    # Velocity
    new_mag('ips', Magnitude(0.0254, m=1, s=-1))
    new_mag('c', Magnitude(2.99792458e8, m=1, s=-1))

    # Acceleration
    new_mag('gravity', Magnitude(9.80665, m=1, s=-2))

    # Eric - distance
    new_mag('ang', Magnitude(1.0e-10, m=1))

    # Eric - mass
    new_mag('uma', Magnitude(1.6605402e-27, kg=1))

    # Eric energy
    new_mag('cal', Magnitude(4.184, m=2, kg=1, s=-2))
    new_mag('cal_per_mole', Magnitude(6.94778e-24, m=2, kg=1, s=-2))    
    new_mag('J_per_mole', Magnitude(1.66055927e-24, m=2, kg=1, s=-2))    
    new_mag('eV', Magnitude(1.60217649e-19, m=2, kg=1, s=-2))
    new_mag('Ha', Magnitude(4.35974394e-18, m=2, kg=1, s=-2))
    
    # Eric - frequency
    new_mag('rad_inv_s', Magnitude(2.0*math.pi, s=-1))
    
    # Energy equivalent
    new_mag('inv_m_eq', Magnitude(1.9864455e-25, m=2, kg=1, s=-2))
    new_mag('Hz_eq', Magnitude(6.62606896e-34, m=2, kg=1, s=-2))
    new_mag('K_eq', Magnitude(1.3806504e-23, m=2, kg=1, s=-2))
    new_mag('u_eq', Magnitude(1.49241783e-10, m=2, kg=1, s=-2))

    # Frequency equivalent
    new_mag('J_eq', Magnitude(1.50919045e+33, s=-1))
    new_mag('eV_eq', Magnitude(2.41798945e+14, s=-1))

    # Eric - inverse of distance
    new_mag('inv_m', Magnitude(1.0, m=-1, kg=0, s=0))
    new_mag('inv_m', Magnitude(1.0, m=-1, kg=0, s=0))
    new_mag('inv_um', Magnitude(1.0e6, m=-1, kg=0, s=0))
    new_mag('inv_nm', Magnitude(1.0e9, m=-1, kg=0, s=0))
    new_mag('inv_ang', Magnitude(1.0e10, m=-1, kg=0, s=0))
    
    new_mag('au', Magnitude(1.0))
    new_mag('wu', Magnitude(1.0))
    new_mag('unitless', Magnitude(1.0))
    new_mag('no-unit', Magnitude(1.0))


if not MAGS:
    _init_mags()
    
