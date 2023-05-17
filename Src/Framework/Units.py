import copy
import math
import numbers
import os

import yaml

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Singleton import Singleton

_UNAMES = ['kg', 'm', 's', 'K', 'mol', 'A', 'cd', 'rad', 'sr']
_PREFIXES = {'y': 1e-24,  # yocto
             'z': 1e-21,  # zepto
             'a': 1e-18,  # atto
             'f': 1e-15,  # femto
             'p': 1e-12,  # pico
             'n': 1e-9,   # nano
             'u': 1e-6,   # micro
             'm': 1e-3,   # mili
             'c': 1e-2,   # centi
             'd': 1e-1,   # deci
             'da':1e1,    # deka
             'h': 1e2,    # hecto
             'k': 1e3,    # kilo
             'M': 1e6,    # mega
             'G': 1e9,    # giga
             'T': 1e12,   # tera
             'P': 1e15,   # peta
             'E': 1e18,   # exa
             'Z': 1e21,   # zetta
             'Y': 1e24,   # yotta
        }

class UnitError(Exception):
    pass

def get_trailing_digits(s):

    for i in range(len(s)):
        if s[i:].isdigit():
            return s[:i],int(s[i:])
    else:
        return s, 1

def _parse_unit(iunit):
    
    max_prefix_length = 0
    for p in _PREFIXES:
        max_prefix_length = max(max_prefix_length,len(p))

    iunit = iunit.strip()

    iunit,upower = get_trailing_digits(iunit)
    if not iunit:
        raise UnitError('Invalid unit')

    for i in range(len(iunit)):
        if UNITS_MANAGER.has_unit(iunit[i:]):
            prefix = iunit[:i]
            iunit = iunit[i:]
            break
    else:
       raise UnitError('The unit {} is unknown'.format(iunit))

    if prefix:
        if prefix not in _PREFIXES:
           raise UnitError('The prefix {} is unknown'.format(prefix))
        prefix = _PREFIXES[prefix]
    else:
        prefix = 1.0
    
    unit = UNITS_MANAGER.get_unit(iunit)

    unit = _Unit(iunit,prefix*unit._factor,*unit._dimension)
    
    unit **= upower
        
    return unit
    
def _str_to_unit(s):

    if UNITS_MANAGER.has_unit(s):
        unit = UNITS_MANAGER.get_unit(s)
        return copy.deepcopy(unit)

    else:

        unit = _Unit('au',1.0)

        splitted_units = s.split('/')
        
        if len(splitted_units) == 1:        
            units = splitted_units[0].split(' ')
            for u in units:
                u = u.strip()
                unit *= _parse_unit(u)
            unit._uname = s
                                
            return unit
            
        elif len(splitted_units) == 2:
            numerator = splitted_units[0].strip()
            if numerator != '1':
                numerator = numerator.split(' ')
                for u in numerator:
                    u = u.strip()
                    unit *= _parse_unit(u)

            denominator = splitted_units[1].strip().split(' ')
            for u in denominator:
                u = u.strip()
                unit /= _parse_unit(u)

            unit._uname = s

            return unit
            
        else:
            raise UnitError('Invalid unit: {}'.format(s))

class _Unit(object):

    def __init__(self, uname, factor, kg=0, m=0, s=0, K=0, mol=0, A=0, cd=0, rad=0, sr=0):
    
        self._factor = factor
        
        self._dimension = [kg,m,s,K,mol,A,cd,rad,sr]
        
        self._format = 'g'

        self._uname = uname

        self._ounit = None

        self._out_factor = None

        self._equivalent = False

    def __add__(self, other):
        """Add _Unit instances. To be added, the units has to be analog or equivalent.

        >>> print(measure(10, 'm') + measure(20, 'km'))
        20010 m
        """

        u = copy.deepcopy(self)

        if u.is_analog(other):
            u._factor += other._factor
            return u
        elif self._equivalent:
            equivalence_factor = u.get_equivalence_factor(other)
            if equivalence_factor is not None:
                u._factor += other._factor/equivalence_factor
                return u
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')

    def __div__(self, other):
        """Divide _Unit instances.

        >>> print(measure(100, 'V') / measure(10, 'kohm'))
        0.0100 A
        """
    
        u = copy.deepcopy(self)
        if isinstance(other,numbers.Number):
            u._factor /= other
            return u
        elif isinstance(other,_Unit):
            u._div_by(other)
            return u
        else:
            raise UnitError('Invalid operand')

    def __float__(self):
        """Return the value of a _Unit coerced to float.  See __int__."""
    
        return float(self.toval())

    def __floordiv__(self, other):

        u = copy.deepcopy(self)
        u._div_by(other)
        u._factor = math.floor(u._factor)
        return u

    def __iadd__(self, other):
        """Add _Unit instances.  See __add__. """

        if self.is_analog(other):
            self._factor += other._factor
            return self
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is not None:
                self._factor += other._factor/equivalence_factor
                return self
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')

    def __idiv__(self, other):
        """Divide _Unit instances.  See __div__. """
    
        if isinstance(other,numbers.Number):
            self._factor /= other
            return self
        elif isinstance(other,_Unit):
            self._div_by(other)
            return self
        else:
            raise UnitError('Invalid operand')

    def __ifloordiv__(self, other):

        self._div_by(other)
        self._factor = math.floor(self._factor)
        return self

    def __imul__(self, other):
        """Multiply _Unit instances.  See __mul__. """

        if isinstance(other,numbers.Number):
            self._factor *= other
            return self
        elif isinstance(other,_Unit):
            self._mult_by(other)
            return self
        else:
            raise UnitError('Invalid operand')

    def __int__(self):
        """Return the value of a _Unit coerced to integer.

        Note that this will happen to the value in the default output unit:

        >>> print(int(measure(10.5, 'm/s')))
        10
        """
    
        return int(self.toval())

    def __ipow__(self, n):
        self._factor = pow(self._factor, n)
        for i in range(len(self._dimension)):
            self._dimension[i] *= n

        self._ounit = None
        self._out_factor = None

        return self

    def __isub__(self, other):
        """Substract _Unit instances.  See __sub__. """

        if self.is_analog(other):
            self._factor -= other._factor
            return self
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is not None:
                self._factor -= other._factor/equivalence_factor
                return self
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')

    def __mul__(self, other):
        """Multiply _Unit instances.

        >>> print(measure(10, 'm/s') * measure(10, 's'))
        100.0000 m
        """

        u = copy.deepcopy(self)
        if isinstance(other,numbers.Number):
            u._factor *= other
            return u
        elif isinstance(other,_Unit):
            u._mult_by(other)
            return u
        else:
            raise UnitError('Invalid operand')

    def __pow__(self, n):
        output_unit = copy.copy(self)
        output_unit._ounit = None
        output_unit._out_factor = None
        output_unit._factor = pow(output_unit._factor, n)
        for i in range(len(output_unit._dimension)):
            output_unit._dimension[i] *= n

        return output_unit

    def __radd__(self, other):
        """Add _Unit instances.  See __add__. """

        return self.__add__(other)

    def __rdiv__(self, other):
    
        u = copy.deepcopy(self)
        if isinstance(other,numbers.Number):
            u._factor /= other
            return u
        elif isinstance(other,_Unit):
            u._div_by(other)
            return u
        else:
            raise UnitError('Invalid operand')

    def __rmul__(self, other):
        """Multiply _Unit instances.  See __mul__. """
    
        u = copy.deepcopy(self)
        if isinstance(other,numbers.Number):
            u._factor *= other
            return u
        elif isinstance(other,_Unit):
            u._mult_by(other)
            return u
        else:
            raise UnitError('Invalid operand')

    def __rsub__(self, other):
        """Substract _Unit instances.  See __sub__. """

        return other.__sub__(self)

    def __sub__(self, other):
        """Substract _Unit instances. To be substracted, the units has to be analog or equivalent.

        >>> print(measure(20, 'km') + measure(10, 'm'))
        19990 m
        """

        u = copy.deepcopy(self)

        if u.is_analog(other):
            u._factor -= other._factor
            return u
        elif u._equivalent:
            equivalence_factor = u.get_equivalence_factor(other)
            if equivalence_factor is not None:
                u._factor -= other._factor/equivalence_factor
                return u
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')

    def __str__(self):

        unit = copy.copy(self)

        fmt = '{:%s}' % self._format

        if self._ounit is None:

            s = fmt.format(unit._factor)

            positive_units = []
            negative_units = []
            for uname,uval in zip(_UNAMES,unit._dimension):
                if uval == 0:
                    continue
                elif uval > 0:
                    if uval == 1:
                        positive_units.append("{:s}".format(uname))
                    else:
                        if uval.is_integer():
                            positive_units.append("{:s}{:d}".format(uname,int(uval)))
                        else:
                            positive_units.append("{:s}{}".format(uname,uval))
                elif uval < 0:
                    if uval == -1:
                        negative_units.append("{:s}".format(uname))
                    else:
                        if uval.is_integer():
                            negative_units.append("{:s}{:d}".format(uname,int(-uval)))
                        else:
                            negative_units.append("{:s}{}".format(uname,-uval))

            positive_units_str = ''                
            if positive_units:
                positive_units_str = ' '.join(positive_units)
            
            negative_units_str = ''                
            if negative_units:
                negative_units_str = ' '.join(negative_units)

            if positive_units_str:
                s += ' {:s}'.format(positive_units_str)
                
            if negative_units_str:
                if not positive_units_str:
                    s += ' 1' 
                s += ' / {}'.format(negative_units_str)
                    
        else:

            u = copy.deepcopy(self)
            u._div_by(self._out_factor)

            s = fmt.format(u._factor)
            s += ' {}'.format(self._ounit)

        return s

    def _div_by(self, other):

        if self.is_analog(other):
            self._factor /= other._factor
            self._dimension = [0,0,0,0,0,0,0,0,0]        
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is not None:
                self._factor /= other._factor/equivalence_factor
                self._dimension = [0,0,0,0,0,0,0,0,0]
            else:
                raise UnitError('The units are not equivalent')
        else:
            self._factor /= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = self._dimension[i] - other._dimension[i]

        self._ounit = None
        self._out_factor = None

    def _mult_by(self, other):

        if self.is_analog(other):
            self._factor *= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = 2.0*self._dimension[i]
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is not None:
                self._factor *= other._factor/equivalence_factor
                for i in range(len(self._dimension)):
                    self._dimension[i] = 2*self._dimension[i]
                return
            else:
                raise UnitError('The units are not equivalent')
        else:
            self._factor *= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = self._dimension[i] + other._dimension[i]

        self._ounit = None
        self._out_factor = None

    def ceil(self):
        """Ceil of a _Unit value in canonical units. 

        >>> print(measure(10.2, 'm/s').ceiling())
        10.0000 m / s
        >>> print(measure(3.6, 'm/s').ounit('km/h').ceiling())
        10.0 km / h
        >>> print(measure(50.3, 'km/h').ceiling())
        50.0 km / h
        """

        r = copy.deepcopy(self)

        if r._ounit is not None:
            val = math.ceil(r.toval(r._ounit))
            newu = _Unit('au',val)
            newu *= _str_to_unit(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = math.ceil(r._factor)
            return r

    @property
    def dimension(self):
        """Getter for _dimension attribute. Returns a copy.
        """

        return copy.copy(self._dimension)

    @property
    def equivalent(self):
        """Getter for _equivalent attribute.
        """

        return self._equivalent

    @equivalent.setter
    def equivalent(self, equivalent):
        """Setter for _equivalent attribute.
        """

        self._equivalent = equivalent

    @property
    def factor(self):
        """Getter for _factor attribute.
        """

        return self._factor

    def floor(self):
        """Floor of a _Unit value in canonical units. 

        >>> print(measure(10.2, 'm/s').floor())
        10.0000 m / s
        >>> print(measure(3.6, 'm/s').ounit('km/h').floor())
        10.0 km / h
        >>> print(measure(50.3, 'km/h').floor())
        50.0 km / h
        """

        r = copy.deepcopy(self)

        if r._ounit is not None:
            val = math.floor(r.toval(r._ounit))
            newu = _Unit('au',val)
            newu *= _str_to_unit(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = math.floor(r._factor)
            return r

    @property
    def format(self):
        """Getter for the output format.
        """
    
        return self._format

    @format.setter
    def format(self, fmt):
        """Setter for the output format.
        """
    
        self._format = fmt

    def is_analog(self,other):
        """Returns True if the other unit is analog to this unit. Analog units are units whose dimension vector exactly matches.
        """
        return self._dimension == other._dimension

    def get_equivalence_factor(self,other):
        """Returns the equivalence factor if the other unit is equivalent to this unit. Equivalent units are units whose dimension are related through a constant 
        (e.g. energy and mass, or frequency and temperature).
        """
        
        _,upower = get_trailing_digits(self._uname)
        dimension = tuple([d/upower for d in self._dimension])        
        if dimension not in _EQUIVALENCES:
            return None

        powerized_equivalences = {}
        for k, v in list(_EQUIVALENCES[dimension].items()):
            pk = tuple([d*upower for d in k])
            powerized_equivalences[pk] = pow(v,upower)
           
        odimension = tuple(other._dimension)     
        if odimension in powerized_equivalences:
            return powerized_equivalences[odimension]
        else:
            return None

    def ounit(self, ounit):
        """Set the preferred unit for output.

        >>> a = measure(1, 'kg m2 / s2')
        >>> print(a)
        1.0000 kg m2 / s2
        >>> print(a.ounit('J'))
        1.0000 J
        """

        out_factor = _str_to_unit(ounit)

        if self.is_analog(out_factor):
            self._ounit = ounit
            self._out_factor = out_factor
            return self
        elif self._equivalent:
            if self.get_equivalence_factor(out_factor) is not None:
                self._ounit = ounit
                self._out_factor = out_factor
                return self
            else:
                raise UnitError('The units are not equivalents')
        else:
            raise UnitError('The units are not compatible')

    def round(self):
        """Round of a _Unit value in canonical units. 

        >>> print(measure(10.2, 'm/s').round())
        10.0000 m / s
        >>> print(measure(3.6, 'm/s').ounit('km/h').round())
        11.0 km / h
        >>> print(measure(50.3, 'km/h').round())
        50.0 km / h
        """

        r = copy.deepcopy(self)

        if r._ounit is not None:
            val = round(r.toval(r._ounit))
            newu = _Unit('au',val)
            newu *= _str_to_unit(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = round(r._factor)
            return r

    def sqrt(self):
        """Square root of a _Unit. 

        >>> print(measure(4, 'm2/s2').sqrt())
        2.0000 m / s
        """

        return self ** 0.5

    def toval(self, ounit=''):
        """Returns the numeric value of a unit.

        The value is given in ounit or in the default output unit.

        >>> v = measure(100, 'km/h')
        >>> v.toval()
        100.0
        >>> v.toval(ounit='m/s')
        27.777777777777779
        """

        newu = copy.deepcopy(self)
        if not ounit:
            ounit = self._ounit

        if ounit is not None:
            out_factor = _str_to_unit(ounit)

            if newu.is_analog(out_factor):
                newu._div_by(out_factor)
                return newu._factor
            elif newu._equivalent:
                if newu.get_equivalence_factor(out_factor) is not None:
                    newu._div_by(out_factor)
                    return newu._factor
                else:
                    raise UnitError('The units are not equivalents')
            else:
                raise UnitError('The units are not compatible')
        else:
            return newu._factor

def noop(self, *args, **kw):
    pass

def represent_unit(dumper, data):
    return dumper.represent_mapping("", dict(factor=data._factor,dimension=data._dimension))

yaml.add_representer(_Unit, represent_unit)

process_tag = yaml.emitter.Emitter.process_tag

class UnitsManager(metaclass=Singleton):

    _UNITS = {}

    _DEFAULT_DATABASE = os.path.join(PLATFORM.base_directory(),"MDANSE", "Framework","Units.yml")

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), "Units.yml")

    def __init__(self):

        self.load()

    def add_unit(self, uname, factor, kg=0, m=0, s=0, K=0, mol=0, A=0, cd=0, rad=0, sr=0):

        UnitsManager._UNITS[uname] = _Unit(uname,factor, kg, m, s, K, mol, A, cd, rad, sr)

    def delete_unit(self, uname):

        if uname in UnitsManager._UNITS:
            del UnitsManager._UNITS[uname]

    def get_unit(self, uname):

        return UnitsManager._UNITS.get(uname,None)

    def has_unit(self, uname):

        return uname in UnitsManager._UNITS

    def load(self):

        UnitsManager._UNITS.clear()

        d = {}
        try:
            with open(UnitsManager._USER_DATABASE, 'r') as fin:
                d.update(yaml.safe_load(fin))
        except:
            with open(UnitsManager._DEFAULT_DATABASE, 'r') as fin:
                d.update(yaml.safe_load(fin))
        finally:
            for uname, udict in list(d.items()):
                factor = udict.get('factor',1.0)
                dim = udict.get('dimension',[0,0,0,0,0,0,0,0,0])
                UnitsManager._UNITS[uname] = _Unit(uname,factor,*dim)

    def save(self):

        yaml.emitter.Emitter.process_tag = noop

        try:
            with open(UnitsManager._USER_DATABASE, 'w') as fout:
                yaml.dump(UnitsManager._UNITS, fout, default_flow_style=None)
        finally:
            yaml.emitter.Emitter.process_tag = process_tag

    @property
    def units(self):

        return UnitsManager._UNITS

    @units.setter
    def units(self,units):

        UnitsManager._UNITS = units
                
_EQUIVALENCES = {}

def add_equivalence(dim1,dim2,factor):

    _EQUIVALENCES.setdefault(dim1,{}).__setitem__(dim2,factor)
    _EQUIVALENCES.setdefault(dim2,{}).__setitem__(dim1,1.0/factor)

def measure(val, iunit='au', ounit='',equivalent=False):

    if iunit:
        unit = _str_to_unit(iunit)
        unit *= val
    else:
        unit = _Unit('au',val)

    unit.equivalent = equivalent

    if not ounit:
        ounit = iunit

    unit.ounit(ounit)

    return unit

UNITS_MANAGER = UnitsManager()
# au --> au
add_equivalence((0,0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0,0),1.0)
# 1J --> 1Hz
add_equivalence((1,2,-2,0,0,0,0,0,0),(0,0,-1,0,0,0,0,0,0),1.50919031167677e+33)
# 1J --> 1K
add_equivalence((1,2,-2,0,0,0,0,0,0),(0,0,0,1,0,0,0,0,0),7.242971666663e+22)
# 1J --> 1kg
add_equivalence((1,2,-2,0,0,0,0,0,0),(1,0,0,0,0,0,0,0,0),1.112650055999e-17)
# 1J --> 1/m
add_equivalence((1,2,-2,0,0,0,0,0,0),(0,-1,0,0,0,0,0,0,0),5.034117012218e+24)
# 1J --> 1J/mol
add_equivalence((1,2,-2,0,0,0,0,0,0),(1,2,-2,0,-1,0,0,0,0),6.02214076e+23)
# 1J --> 1rad/s
add_equivalence((1,2,-2,0,0,0,0,0,0),(0,0,-1,0,0,0,0,1,0),9.482522392065263e+33)
# 1Hz --> 1K
add_equivalence((0,0,-1,0,0,0,0,0,0),(0,0,0,1,0,0,0,0,0),4.79924341590788e-11)
# 1Hz --> 1kg
add_equivalence((0,0,-1,0,0,0,0,0,0),(1,0,0,0,0,0,0,0,0),7.37249667845648e-51)
# 1Hz --> 1/m
add_equivalence((0,0,-1,0,0,0,0,0,0),(0,-1,0,0,0,0,0,0,0),3.33564095480276e-09)
# 1Hz --> 1J/mol
add_equivalence((0,0,-1,0,0,0,0,0,0),(1,2,-2,0,-1,0,0,0,0),3.9903124e-10)
# 1Hz --> 1rad/s
add_equivalence((0,0,-1,0,0,0,0,0,0),(0,0,-1,0,0,0,0,1,0),6.283185307179586)
# 1K --> 1kg
add_equivalence((0,0,0,1,0,0,0,0,0),(1,0,0,0,0,0,0,0,0),1.53617894312656e-40)
# 1K --> 1/m
add_equivalence((0,0,0,1,0,0,0,0,0),(0,-1,0,0,0,0,0,0,0),6.95034751466497e+01)
# 1K --> 1J/mol
add_equivalence((0,0,0,1,0,0,0,0,0),(1,2,-2,0,-1,0,0,0,0),8.31435)
# 1K --> 1rad/s
add_equivalence((0,0,0,1,0,0,0,0,0),(0,0,-1,0,0,0,0,1,0),130920329782.73508)
# 1kg --> 1/m
add_equivalence((1,0,0,0,0,0,0,0,0),(0,-1,0,0,0,0,0,0,0),4.52443873532014e+41)
# 1kg --> 1J/mol
add_equivalence((1,0,0,0,0,0,0,0,0),(0,-1,0,0,0,0,0,0,0),5.412430195397762e+40)
# 1kg --> 1rad/s
add_equivalence((1,0,0,0,0,0,0,0,0),(0,0,-1,0,0,0,0,1,0),8.522466107774846e+50)
# 1/m --> 1J/mol
add_equivalence((0,-1,0,0,0,0,0,0,0),(1,2,-2,0,-1,0,0,0,0),0.000119627)
# 1/m --> 1rad/s
add_equivalence((0,-1,0,0,0,0,0,0,0),(0,0,-1,0,0,0,0,1,0),1883651565.7166505)
# 1J/mol --> 1rad/s
add_equivalence((1,2,-2,0,-1,0,0,0,0),(0,0,-1,0,0,0,0,1,0),15746098887.375164)

if __name__ == '__main__':
    m = measure(1.0, 'm')
    m **= 3
