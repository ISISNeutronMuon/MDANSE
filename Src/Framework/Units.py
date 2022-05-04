import copy
import math
import numbers
import os
import string

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

_EQUIVALENCES = {}
_EQUIVALENCES[(0,0,0,0,0,0,0,0,0)] = {}
_EQUIVALENCES[(1, 2,-2,0,0,0,0,0,0)] = {}
_EQUIVALENCES[(0, 0,-1,0,0,0,0,0,0)] = {}
_EQUIVALENCES[(0, 0, 0,1,0,0,0,0,0)] = {}
_EQUIVALENCES[(1, 0, 0,0,0,0,0,0,0)] = {}
_EQUIVALENCES[(0,-1, 0,0,0,0,0,0,0)] = {}
_EQUIVALENCES[(1,2,-2,0,-1,0,0,0,0)] = {}

_EQUIVALENCES[(0,0,0,0,0,0,0,0,0)][(0,0,0,0,0,0,0,0,0)] = 1.0

# 1J --> 1Hz
_EQUIVALENCES[(1,2,-2,0,0,0,0,0,0)][(0,0,-1,0,0,0,0,0,0)] = 1.50919031167677e+33
# 1J --> 1K
_EQUIVALENCES[(1,2,-2,0,0,0,0,0,0)][(0,0,0,1,0,0,0,0,0)] = 7.242971666663e+22
# 1J --> 1kg
_EQUIVALENCES[(1,2,-2,0,0,0,0,0,0)][(1,0,0,0,0,0,0,0,0)] = 1.112650055999e-17
# 1J --> 1/m
_EQUIVALENCES[(1,2,-2,0,0,0,0,0,0)][(0,-1,0,0,0,0,0,0,0)] = 5.034117012218e+24
# 1J --> 1J/mol
_EQUIVALENCES[(1,2,-2,0,0,0,0,0,0)][(1,2,-2,0,-1,0,0,0,0)] = 6.02214076e+23

# 1Hz --> 1J
_EQUIVALENCES[(0,0,-1,0,0,0,0,0,0)][(1,2,-2,0,0,0,0,0,0)] = 6.62606957030801e-34
# 1Hz --> 1K
_EQUIVALENCES[(0,0,-1,0,0,0,0,0,0)][(0,0,0,1,0,0,0,0,0)] = 4.79924341590788e-11
# 1Hz --> 1kg
_EQUIVALENCES[(0,0,-1,0,0,0,0,0,0)][(1,0,0,0,0,0,0,0,0)] = 7.37249667845648e-51
# 1Hz --> 1/m
_EQUIVALENCES[(0,0,-1,0,0,0,0,0,0)][(0,-1,0,0,0,0,0,0,0)] = 3.33564095480276e-09
# 1Hz --> 1J/mol
_EQUIVALENCES[(0,0,-1,0,0,0,0,0,0)][(1,2,-2,0,-1,0,0,0,0)] = 3.9903124e-10

# 1K --> 1J
_EQUIVALENCES[(0,0,0,1,0,0,0,0,0)][(1,2,-2,0,0,0,0,0,0)] = 1.38064878066922e-23
# 1K --> 1Hz
_EQUIVALENCES[(0,0,0,1,0,0,0,0,0)][(0,0,-1,0,0,0,0,0,0)] = 2.08366176361327e+10
# 1K --> 1kg
_EQUIVALENCES[(0,0,0,1,0,0,0,0,0)][(1,0,0,0,0,0,0,0,0)] = 1.53617894312656e-40
# 1K --> 1/m
_EQUIVALENCES[(0,0,0,1,0,0,0,0,0)][(0,-1,0,0,0,0,0,0,0)] = 6.95034751466497e+01
# 1K --> 1J/mol
_EQUIVALENCES[(0,0,0,1,0,0,0,0,0)][(1,2,-2,0,-1,0,0,0,0)] = 8.31435

# 1kg --> 1J
_EQUIVALENCES[(1,0,0,0,0,0,0,0,0)][(1,2,-2,0,0,0,0,0,0)] = 8.98755178780936e+16
# 1kg --> 1Hz
_EQUIVALENCES[(1,0,0,0,0,0,0,0,0)][(0,0,-1,0,0,0,0,0,0)] = 1.35639260838482e+50
# 1kg --> 1K
_EQUIVALENCES[(1,0,0,0,0,0,0,0,0)][(0,0,0,1,0,0,0,0,0)] = 6.50965829517696e+39
# 1kg --> 1/m
_EQUIVALENCES[(1,0,0,0,0,0,0,0,0)][(0,-1,0,0,0,0,0,0,0)] = 4.52443873532014e+41
# 1kg --> 1J/mol
_EQUIVALENCES[(1,0,0,0,0,0,0,0,0)][(0,-1,0,0,0,0,0,0,0)] = 5.412430195397762e+40

# 1/m --> 1J
_EQUIVALENCES[(0,-1,0,0,0,0,0,0,0)][(1,2,-2,0,0,0,0,0,0)] = 1.98644568168154e-25
# 1/m --> 1Hz
_EQUIVALENCES[(0,-1,0,0,0,0,0,0,0)][(0,0,-1,0,0,0,0,0,0)] = 2.9979245774644e+08
# 1/m --> 1K
_EQUIVALENCES[(0,-1,0,0,0,0,0,0,0)][(0,0,0,1,0,0,0,0,0)] = 0.0143877697897844
# 1/m --> kg
_EQUIVALENCES[(0,-1,0,0,0,0,0,0,0)][(1,0,0,0,0,0,0,0,0)] = 2.21021889896193e-42
# 1/m --> 1J/mol
_EQUIVALENCES[(0,-1,0,0,0,0,0,0,0)][(1,2,-2,0,-1,0,0,0,0)] = 0.000119627

# 1J/mol --> 1J
_EQUIVALENCES[(1,2,-2,0,-1,0,0,0,0)][(1,2,-2,0,0,0,0,0,0)] = 1.66054e-24
# 1J/mol --> 1Hz
_EQUIVALENCES[(1,2,-2,0,-1,0,0,0,0)][(0,0,-1,0,0,0,0,0,0)] = 2506070880.151561
# 1J/mol --> 1K
_EQUIVALENCES[(1,2,-2,0,-1,0,0,0,0)][(0,0,0,1,0,0,0,0,0)] = 0.12027244171360577
# 1J/mol --> 1/m
_EQUIVALENCES[(1,2,-2,0,-1,0,0,0,0)][(0,0,0,1,0,0,0,0,0)] = 8.359352663468478
# 1J/mol --> kg
_EQUIVALENCES[(1,2,-2,0,-1,0,0,0,0)][(1,0,0,0,0,0,0,0,0)] = 1.8475999239885794e-41

class UnitError(Exception):
    pass

def get_trailing_digits(s):

    for i in range(len(s)):
        if s[i:] in string.digits:
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

    for i in range(max_prefix_length,0,-1):
        s = iunit[:i]
        if s == iunit:
            continue
        if s in _PREFIXES:
            prefix = _PREFIXES[s]
            iunit = iunit[i:]
            break
    else:
        prefix = 1.0

    if not UNITS_MANAGER.has_unit(iunit):
        raise UnitError('The unit {} is unknown'.format(iunit))
        
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

class _Unit:

    def __init__(self, uname, factor, kg=0, m=0, s=0, K=0, mol=0, A=0, cd=0, rad=0, sr=0):
    
        self._factor = factor
        
        self._dimension = [kg,m,s,K,mol,A,cd,rad,sr]
        
        self._format = 'g'

        self._uname = uname

        self._ounit = None

        self._out_factor = None

        self._equivalent = None

    def set_equivalent(self, equivalent):

        self._equivalent = equivalent

    def _set_unit_name(self):

        num_dimensions = []
        den_dimensions = []
        for i in range(len(_UNAMES)):

            dim = self._dimension[i]
            if dim > 1:                
                num_dimensions.append('{:s}{:d}'.format(_UNAMES[i],dim))
            elif dim == 1:
                num_dimensions.append('{:s}'.format(_UNAMES[i]))
            elif dim == -1:
                den_dimensions.append('{:s}'.format(_UNAMES[i]))
            elif dim < -1:
                den_dimensions.append('{:s}{:d}'.format(_UNAMES[i],-dim))

        if not num_dimensions and not den_dimensions:
            self._uname = None
            return

        if num_dimensions:
            num_dimensions = ' '.join(num_dimensions)
        else:
            num_dimensions = '1'

        if den_dimensions:
            den_dimensions = ' '.join(den_dimensions)
            num_dimensions += ' / {:s}'.format(den_dimensions)

        self._uname = num_dimensions

    def set_format(self, fmt):
    
        self._format = fmt

    def __int__(self):
    
        return int(self._factor)
    
    def __float__(self):
    
        return float(self._factor)

    @staticmethod
    def _build_unit_from_dimension(dimension):

        num_dimensions = []
        den_dimensions = []
        for i in range(len(_UNAMES)):
            dim = dimension[i]
            if dim > 1:                
                num_dimensions.append('{:s}{:d}'.format(_UNAMES[i],dim))
            elif dim == 1:
                num_dimensions.append('{:s}'.format(_UNAMES[i]))
            elif dim == -1:
                den_dimensions.append('{:s}'.format(_UNAMES[i]))
            elif dim < -1:
                den_dimensions.append('{:s}{:d}'.format(_UNAMES[i],-dim))

        if not num_dimensions and not den_dimensions:
            
            return None

        if num_dimensions:
            num_dimensions = ' '.join(num_dimensions)
        else:
            num_dimensions = '1'

        if den_dimensions:
            den_dimensions = ' '.join(den_dimensions)
            num_dimensions += ' / {:s}'.format(den_dimensions)

        return num_dimensions

    def _mult_by(self, other):

        if self.is_compatible(other):
            self._factor *= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = 2*self._dimension[i]
        elif other._equivalent:
            if self.is_equivalent(other):
                dim = tuple(self._dimension)
                other_dim = tuple(other._dimension)
                conv_fact = _EQUIVALENCES[dim][other_dim]
                self._factor *= other._factor/conv_fact
                for i in range(len(self._dimension)):
                    self._dimension[i] = 2*self._dimension[i]
            else:
                raise UnitError('The units are not equivalent')
        else:
            self._factor *= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = self._dimension[i] + other._dimension[i]

        self._ounit = None
        self._out_factor = None

    def _div_by(self, other):

        if self.is_compatible(other):
            self._factor /= other._factor
            self._dimension = [0,0,0,0,0,0,0,0,0]
        elif other._equivalent:
            if self.is_equivalent(other):
                dim = tuple(self._dimension)
                other_dim = tuple(other._dimension)
                conv_fact = _EQUIVALENCES[dim][other_dim]
                self._factor /= other._factor/conv_fact
                self._dimension = [0,0,0,0,0,0,0,0,0]
            else:
                raise UnitError('The units are not equivalent')
        else:
            self._factor /= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = self._dimension[i] - other._dimension[i]

        self._ounit = None
        self._out_factor = None

    def __add__(self, other):

        u = copy.deepcopy(self)

        if u.is_compatible(other):
            u._factor += other._factor
            return u
        elif other._equivalent:
            if u.is_equivalent(other):
                dim = tuple(u._dimension)
                other_dim = tuple(other._dimension)
                conv_fact = _EQUIVALENCES[dim][other_dim]
                u._factor += other._factor/conv_fact
                return u
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')

    def __radd__(self, other):

        return self.__add__(other)

    def __iadd__(self, other):

        if self.is_compatible(other):
            self._factor += other._factor
            return self
        elif other._equivalent:
            if self.is_equivalent(other):
                dim = tuple(self._dimension)
                other_dim = tuple(other._dimension)
                conv_fact = _EQUIVALENCES[dim][other_dim]
                self._factor += other._factor/conv_fact
                return self
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')
    
    def __sub__(self, other):

        u = copy.deepcopy(self)

        if u.is_compatible(other):
            u._factor -= other._factor
            return u
        elif other._equivalent:
            if u.is_equivalent(other):
                dim = tuple(u._dimension)
                other_dim = tuple(other._dimension)
                conv_fact = _EQUIVALENCES[dim][other_dim]
                u._factor -= other._factor/conv_fact
                return u
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')

    def __rsub__(self, other):

        return other.__sub__(self)

    def __isub__(self, other):

        if self.is_compatible(other):
            self._factor -= other._factor
            return self
        elif other._equivalent:
            if self.is_equivalent(other):
                dim = tuple(self._dimension)
                other_dim = tuple(other._dimension)
                conv_fact = _EQUIVALENCES[dim][other_dim]
                self._factor -= other._factor/conv_fact
                return self
            else:
                raise UnitError('The units are not equivalent')                
        else:
            raise UnitError('Incompatible units')

    def __imul__(self, other):

        if isinstance(other,numbers.Number):
            self._factor *= other
            return self
        elif isinstance(other,_Unit):
            self._mult_by(other)
            return self
        else:
            raise UnitError('Invalid operand')

    def __mul__(self, other):

        u = copy.deepcopy(self)
        if isinstance(other,numbers.Number):
            u._factor *= other
            return u
        elif isinstance(other,_Unit):
            u._mult_by(other)
            return u
        else:
            raise UnitError('Invalid operand')

    def __rmul__(self, other):
    
        u = copy.deepcopy(self)
        if isinstance(other,numbers.Number):
            u._factor *= other
            return u
        elif isinstance(other,_Unit):
            u._mult_by(other)
            return u
        else:
            raise UnitError('Invalid operand')
        
    def __idiv__(self, other):
    
        if isinstance(other,numbers.Number):
            self._factor /= other
            return self
        elif isinstance(other,_Unit):
            self._div_by(other)
            return self
        else:
            raise UnitError('Invalid operand')
            
    def __div__(self, other):
    
        u = copy.deepcopy(self)
        if isinstance(other,numbers.Number):
            u._factor /= other
            return u
        elif isinstance(other,_Unit):
            u._div_by(other)
            return u
        else:
            raise UnitError('Invalid operand')

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

    def __floordiv__(self, other):

        u = copy.deepcopy(self)
        u._div_by(other)
        u._factor = math.floor(u._factor)
        return u

    def __ifloordiv__(self, other):

        self._div_by(other)
        self._factor = math.floor(self._factor)
        return self
              
    def __pow__(self, n, modulo=None):
        output_unit = copy.copy(self)
        if modulo and (output_unit._factor == math.floor(output_unit._factor)):
            output_unit._factor = int(output_unit._factor)
        output_unit._factor = pow(output_unit._factor, n, modulo)
        for i in range(len(output_unit._dimension)):
            output_unit._dimension[i] *= n

        if output_unit._uname is not None:
            if n > 0:
                output_unit._uname = '{:s}{:d}'.format(output_unit._uname,n)
            elif n == 0:
                output_unit._uname = None
            else:
                output_unit._uname = '1 / {:s}{:d}'.format(output_unit._uname,-n)

        return output_unit

    def __ipow__(self, n):
        self._factor = pow(self._factor, n)
        for i in range(len(self._dimension)):
            self._dimension[i] *= n

        if self._uname is not None:
            if n > 0:
                self._uname = '{:s}{:d}'.format(self._uname,n)
            elif n == 0:
                self._uname = None
            else:
                self._uname = '1 / {:s}{:d}'.format(self._uname,-n)

        return self

    def to_val(self):

        if self._uname is None:
            return self._val

        else:
            u = _str_to_unit(self._uname)
            return self._val/u._val

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
                elif uval == 1:
                    positive_units.append("{:s}".format(uname))
                elif uval > 1:
                    positive_units.append("{:s}{:d}".format(uname,uval))
                elif uval == -1:
                    negative_units.append("{:s}".format(uname))
                elif uval < 1:
                    negative_units.append("{:s}{:d}".format(uname,uval))

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

    def is_compatible(self,other):
        return self._dimension == other._dimension

    def find_equivalence(self, other):

        if tuple(self._dimension) not in _EQUIVALENCES:
            return None

        if tuple(other._dimension) in _EQUIVALENCES[tuple(self._dimension)]:
            return _EQUIVALENCES[tuple(self._dimension)][tuple(other._dimension)]
            
        return None

    def is_equivalent(self,other):
        
        _,upower = get_trailing_digits(self._uname)
        print(self._uname,' ---', self._dimension)
        dimension = tuple([d/upower for d in self._dimension])        
        print(self._uname,' ---', dimension)
        if dimension not in _EQUIVALENCES:
            return None

        powerized_equivalences = {}
        for k, v in _EQUIVALENCES[dimension].items():
            pk = tuple([d*upower for d in k])
            powerized_equivalences[pk] = pow(v,upower)
           
        odimension = tuple(other._dimension)     
        print(odimension)
        if odimension in powerized_equivalences:
            return powerized_equivalences[odimension]
        else:
            return None
        
    @staticmethod
    def conversion_factor(u1,u2):

        u1 = _str_to_unit(u1)
        u2 = _str_to_unit(u2)

        if u1.is_compatible(u2):
            return u1._factor/u2._factor
        else:
            factor = u1.is_equivalent(u2)
            if factor is not None:
                return factor*u1._factor/u2._factor
            else:
                raise UnitError('Incompatible units')

    def ounit(self, ounit, equivalent=False):

        self._ounit = ounit
        self._out_factor = _str_to_unit(ounit)
        self._out_factor.set_equivalent(equivalent)

        return self

    def toval(self, ounit='',equivalent=False):

        u = copy.deepcopy(self)
        if not ounit:
            ounit = self._ounit
        if ounit:
            out_factor = _str_to_unit(ounit)
            out_factor.set_equivalent(equivalent)
            u._div_by(out_factor)
        return u._factor

class UnitsManager:

    __metaclass__ = Singleton

    _UNITS = {}

    _DEFAULT_DATABASE = os.path.join(PLATFORM.base_directory(),"MDANSE", "Framework","Units.yml")

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), "Units.yml")

    def __init__(self):

        self.load()

    def add_unit(self, uname, factor, kg=0, m=0, s=0, K=0, mol=0, A=0, cd=0, rad=0, sr=0):

        UnitsManager._UNITS[uname] = _Unit(uname,factor, kg, m, s, K, mol, A, cd, rad, sr)

    def delete_unit(self, uname):

        if UnitsManager._UNITS.has_key(uname):
            del UnitsManager._UNITS[uname]

    def has_unit(self, uname):

        return uname in UnitsManager._UNITS

    def get_unit(self, uname):

        return UnitsManager._UNITS.get(uname,None)

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
            for uname, udict in d.items():
                factor = udict.get('factor',1.0)
                dim = udict.get('dimension',[0,0,0,0,0,0,0,0,0])
                UnitsManager._UNITS[uname] = _Unit(uname,factor,*dim)
                
    def save(self):

        try:
            with open(UnitsManager._USER_DATABASE, 'w') as fout:
                yaml.dump(fout, UnitsManager._UNITS, default_flow_style=None)
        except:
            return

UNITS_MANAGER = UnitsManager()

def measure(val, iunit='au', ounit='', equivalent=False):

    unit = _Unit('au',val)
    if iunit:        
        u = _str_to_unit(iunit)
        unit._mult_by(u)

    unit.set_equivalent(equivalent)

    if not ounit:
        ounit = iunit

    unit.ounit(ounit)

    return unit

if __name__ == '__main__':
    
    m = measure(1.0,'THz')
    print(m.toval('eV',equivalent=True))
