
from qtpy.QtWidgets import QDialog, QToolButton, QFrame, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication

from MDANSE.Chemistry import ATOMS_DATABASE
# from MDANSE.GUI.ElementsDatabaseEditor import ElementsDatabaseEditor

_LAYOUT = {} 
_LAYOUT["H"]   = (0,1) 
_LAYOUT["He"]  = (0,18)

_LAYOUT["Li"]  = (1,1)
_LAYOUT["Be"]  = (1,2)
_LAYOUT["B"]   = (1,13)
_LAYOUT["C"]   = (1,14)
_LAYOUT["N"]   = (1,15)
_LAYOUT["O"]   = (1,16)
_LAYOUT["F"]   = (1,17)
_LAYOUT["Ne"]  = (1,18)

_LAYOUT["Na"]  = (2,1)
_LAYOUT["Mg"]  = (2,2)
_LAYOUT["Al"]  = (2,13)
_LAYOUT["Si"]  = (2,14)
_LAYOUT["P"]   = (2,15)
_LAYOUT["S"]   = (2,16)
_LAYOUT["Cl"]  = (2,17)
_LAYOUT["Ar"]  = (2,18)

_LAYOUT["K"]   = (3,1)
_LAYOUT["Ca"]  = (3,2)
_LAYOUT["Sc"]  = (3,3)
_LAYOUT["Ti"]  = (3,4)
_LAYOUT["V"]   = (3,5)
_LAYOUT["Cr"]  = (3,6)
_LAYOUT["Mn"]  = (3,7)
_LAYOUT["Fe"]  = (3,8)
_LAYOUT["Co"]  = (3,9)
_LAYOUT["Ni"]  = (3,10)
_LAYOUT["Cu"]  = (3,11)
_LAYOUT["Zn"]  = (3,12)
_LAYOUT["Ga"]  = (3,13)
_LAYOUT["Ge"]  = (3,14)
_LAYOUT["As"]  = (3,15)
_LAYOUT["Se"]  = (3,16)
_LAYOUT["Br"]  = (3,17)
_LAYOUT["Kr"]  = (3,18)

_LAYOUT["Rb"]  = (4,1)
_LAYOUT["Sr"]  = (4,2)
_LAYOUT["Y"]   = (4,3)
_LAYOUT["Zr"]  = (4,4)
_LAYOUT["Nb"]  = (4,5)
_LAYOUT["Mo"]  = (4,6)
_LAYOUT["Tc"]  = (4,7)
_LAYOUT["Ru"]  = (4,8)
_LAYOUT["Rh"]  = (4,9)
_LAYOUT["Pd"]  = (4,10)
_LAYOUT["Ag"]  = (4,11)
_LAYOUT["Cd"]  = (4,12)
_LAYOUT["In"]  = (4,13)
_LAYOUT["Sn"]  = (4,14)
_LAYOUT["Sb"]  = (4,15)
_LAYOUT["Te"]  = (4,16)
_LAYOUT["I"]   = (4,17)
_LAYOUT["Xe"]  = (4,18)

_LAYOUT["Cs"]  = (5,1)
_LAYOUT["Ba"]  = (5,2)
_LAYOUT["Hf"]  = (5,4)
_LAYOUT["Ta"]  = (5,5)
_LAYOUT["W"]   = (5,6)
_LAYOUT["Re"]  = (5,7)
_LAYOUT["Os"]  = (5,8)
_LAYOUT["Ir"]  = (5,9)
_LAYOUT["Pt"]  = (5,10)
_LAYOUT["Au"]  = (5,11)
_LAYOUT["Hg"]  = (5,12)
_LAYOUT["Tl"]  = (5,13)
_LAYOUT["Pb"]  = (5,14)
_LAYOUT["Bi"]  = (5,15)
_LAYOUT["Po"]  = (5,16)
_LAYOUT["At"]  = (5,17)
_LAYOUT["Rn"]  = (5,18)

_LAYOUT["Fr"]  = (6,1)
_LAYOUT["Ra"]  = (6,2)
_LAYOUT["Rf"]  = (6,4)
_LAYOUT["Db"]  = (6,5)
_LAYOUT["Sg"]  = (6,6)
_LAYOUT["Bh"]  = (6,7)
_LAYOUT["Hs"]  = (6,8)
_LAYOUT["Mt"]  = (6,9)
_LAYOUT["Ds"]  = (6,10)
_LAYOUT["Rg"]  = (6,11)
_LAYOUT["Cn"]  = (6,12)
_LAYOUT["Nh"]  = (6,13)
_LAYOUT["Fl"]  = (6,14)
_LAYOUT["Mc"]  = (6,15)
_LAYOUT["Lv"]  = (6,16)
_LAYOUT["Ts"]  = (6,17)
_LAYOUT["Og"]  = (6,18)

_LAYOUT["La"]  = (8,4)
_LAYOUT["Ce"]  = (8,5)
_LAYOUT["Pr"]  = (8,6)
_LAYOUT["Nd"]  = (8,7)
_LAYOUT["Pm"]  = (8,8)
_LAYOUT["Sm"]  = (8,9)
_LAYOUT["Eu"]  = (8,10)
_LAYOUT["Gd"]  = (8,11)
_LAYOUT["Tb"]  = (8,12)
_LAYOUT["Dy"]  = (8,13)
_LAYOUT["Ho"]  = (8,14)
_LAYOUT["Er"]  = (8,15)
_LAYOUT["Tm"]  = (8,16)
_LAYOUT["Yb"]  = (8,17)
_LAYOUT["Lu"]  = (8,18)

_LAYOUT["Ac"]  = (9,4)
_LAYOUT["Th"]  = (9,5)
_LAYOUT["Pa"]  = (9,6)
_LAYOUT["U"]   = (9,7)
_LAYOUT["Np"]  = (9,8)
_LAYOUT["Pu"]  = (9,9)
_LAYOUT["Am"]  = (9,10)
_LAYOUT["Cm"]  = (9,11)
_LAYOUT["Bk"]  = (9,12)
_LAYOUT["Cf"]  = (9,13)
_LAYOUT["Es"]  = (9,14)
_LAYOUT["Fm"]  = (9,15)
_LAYOUT["Md"]  = (9,16)
_LAYOUT["No"]  = (9,17)
_LAYOUT["Lr"]  = (9,18)

_COLS = range(1,19)
_ROWS = ["i","ii","iii","iv","v","vi","vii"]

# Dictionary that maps the chemical family with a RGB color.
_FAMILY = {'default' : (128, 128, 128),
           'user-defined' : (255, 255, 255),
           'non metal' : (153, 255, 153),
           'noble gas' : (192, 255, 255),
           'alkali metal' : (255, 153, 153),
           'alkaline earth metal' : (255, 222, 173),
           'metalloid' : (204, 204, 153),
           'halogen' : (255, 255, 153),
           'post-transition metal' : (204, 204, 204),
           'transition metal' : (255, 192, 192),
           'lanthanoid' : (255, 191, 255),
           'actinoid' : (255, 153, 294)}
    
# Dictionary that maps the chemical state with a RGB color.
_STATE = {'default' : (128, 128, 128),
          'user-defined' : (255,0,0),
          'gas' : (255,0,0),
          'liquid' : (0,0,255),
          'solid' : (0,0,0),
          'unknown' : (0,150,0)}


class ElementButton(QToolButton):

    def __init__(self, *args, element = 'Xx', **kwargs):
        super().__init__(*args, **kwargs)

        # try:
        #     chemical_element = kwargs['element']
        # except KeyError:
        #     chemical_element = 'Xx'
        
        self.setText(element)


class PeriodicTableViewer(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Periodic Table of Elements")

        self.glayout = QGridLayout(self)
        self.setLayout(self.glayout)

        self.placeElements()

    def placeElements(self):

        for key, value in _LAYOUT.items():
            element = ElementButton(self, element=key)
            row, column = value[0] + 1, value[1] + 1
            self.glayout.addWidget(element,row,column)

        # for col_num in range(19):
        #     for row_num in range(10):

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    root = PeriodicTableViewer()
    root.show()
    app.exec()
