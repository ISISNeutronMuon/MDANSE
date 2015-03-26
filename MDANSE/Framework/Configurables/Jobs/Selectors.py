import abc
import operator
import os

from MMTK.NucleicAcids import NucleotideChain
from MMTK.PDB import PDBConfiguration
from MMTK.Proteins import PeptideChain, Protein

from MDANSE import PLATFORM,REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Externals.pyparsing.pyparsing import delimitedList, oneOf, opAssoc, operatorPrecedence, printables, Forward, OneOrMore, Optional, Word

# Dictionnary associating tuples of residue names (values) to their corresponding chemical family (key). 
CHEMFAMILIES = {'acidic'      : ('asp','glu'),
                'aliphatic'   : ('ile','leu','val'),
                'aromatic'    : ('his','phe','trp','tyr'),
                'basic'       : ('arg','his','lys'),
                'charged'     : ('arg','asp','glu','his','lys'),
                'hydrophobic' : ('ala','cys','cyx','gly','his','ile','leu','lys','met','phe','thr','trp','tyr','val'),
                'polar'       : ('arg','asn','asp','cys','gln','glu','his','lys','ser','thr','trp','tyr'),
                'small'       : ('ala','asn','asp','cys','cyx','gly','pro','ser','thr','val')}

class SelectorError(Error):
    pass

class SelectionParserError(Error):
    pass

class SelectionParser(object):
        
    def __init__(self, universe):
        
        self._universe = universe
                
    def operator_and(self, token):
        
        token[0][1] = "&"
        
        return " ".join(token[0])

    def operator_not(self, token):
                                
        return 'REGISTRY[%r]("all",universe).select() - %s' % ("selector",token[0][1])

    def operator_or(self, token):
        
        token[0][1] = "|"
            
        return " ".join(token[0])
    
    def parse_arguments(self,token):

        return "(%s)" % str(token)

    def parse_expression(self, token):
                        
        return "".join([str(t) for t in token])
    
    def parse_keyword(self, token):
                            
        return 'REGISTRY[%r]("%s",universe).select' % ("selector",token[0])
    
    def parse_selection_expression(self, expression):
                
        expression = expression.replace("(","( ")
        expression = expression.replace(")"," )")
        
        linkers   = oneOf(["and","&","or","|","not","~"], caseless=True)
        keyword   = oneOf(REGISTRY["selector"].keys(), caseless=True).setParseAction(self.parse_keyword)
        arguments = Optional(~linkers + delimitedList(Word(printables,excludeChars=","),combine=False)).setParseAction(self.parse_arguments)
        
        selector = OneOrMore((keyword+arguments))
        
        grammar = Forward()
        
        grammar << selector.setParseAction(self.parse_expression)

        grammar = operatorPrecedence(grammar, [(oneOf(["and","&"],caseless=True), 2, opAssoc.LEFT , self.operator_and),
                                               (oneOf(["not","~"],caseless=True), 1, opAssoc.RIGHT, self.operator_not),
                                               (oneOf(["or","|"] ,caseless=True), 2, opAssoc.LEFT , self.operator_or)],
                                     lpar="(",
                                     rpar=")")
        
        try:          
            parsedExpression = grammar.transformString(expression)
            namespace={"REGISTRY":REGISTRY,"universe":self._universe}
            selection = eval(parsedExpression,namespace)
        except:
            raise SelectionParserError("%r is not a valid selection string expression" % expression)
        
        selection = sorted(selection, key=operator.attrgetter("index"))
                                
        return selection 
                                                                                                        
    def __call__(self, expression=None, indexes=False):

        if expression is None:
            expression = "all()"
                                    
        # Perfom the actual selection.
        selection = self.parse_selection_expression(expression)
                            
        if not selection:
            raise SelectionParserError("No atoms matched the selection %r." % expression)
        
        selection = [s for s in selection]
        
        if indexes:
            selection = [at.index for at in selection]
        
        return (expression,selection)
            
    select = __call__

class Selector(object):

    __metaclass__ = REGISTRY
    
    type = "selector"
        
    def __init__(self,universe):
        
        self._universe = universe
                
        self._choices = ["*"]

    @property
    def choices(self):
        return self._choices

    @abc.abstractmethod
    def select(self):
        pass

class All(Selector):

    type = "all"

    section = "miscellaneous"
                    
    def select(self, *args):
        return set(self._universe.atomList())
                    
class Amine(Selector):
    '''
    Returns the amine atoms.
    '''

    type = "amine"

    section = "chemical groups"

    def select(self, *args):

        sel = set()
            
        for obj in self._universe.objectList():
                                        
            nitrogens = [at for at in obj.atomList() if at.type.name.strip().lower() == 'nitrogen']
            
            for nit in nitrogens:
                neighbours = nit.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                if len(hydrogens) == 2:
                    sel.update([nit] + [hyd for hyd in hydrogens])
                    
        return sel

class AtomType(Selector):

    type = "atomtype"

    section = "atoms"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        self._choices.extend(sorted(set([at.type.name.lower() for at in self._universe.atomList()])))

    def select(self, elements):
        '''
        Returns the atoms that matches a given list of elements.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param elements: the atom elements list.
        @type elements: list
        '''
                
        sel = set()
                
        if '*' in elements:

            sel.update([at for at in self._universe.atomList()])
        
        else:
            
            vals = [v.lower() for v in elements]
                
            if "sulfur" in vals:
                vals.append("sulphur")
            else:                    
                if "sulphur" in vals:
                    vals.append("sulfur")
                
            vals = set(vals)
            
            sel.update([at for at in self._universe.atomList() if at.type.name.strip().lower() in vals])

        return sel
                
class AtomFullName(Selector):

    type = "atomfullname"

    section = "atoms"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        self._choices.extend(sorted(set([at.fullName().strip().lower() for at in self._universe.atomList()])))

    def select(self, names):
        '''
        Returns the atoms that matches a given list of atom names.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the atom names list.
        @type names: list
        '''
        
        sel = set()

        if '*' in names:

            sel.update([at for at in self._universe.atomList()])
            
        else:
            
            vals = set([v.lower() for v in names])
            sel.update([at for at in self._universe.atomList() if at.fullName().strip().lower() in vals])
        
        return sel

class AtomIndex(Selector):

    type = "atomindex"

    section = "atoms"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        self._choices.extend(sorted([at.index for at in self._universe.atomList()]))


    def select(self, indexes):
        '''
        Returns the atoms that matches a given list of indexes.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param indexes: the atom indexes list.
        @type indexes: list
        '''
        
        sel = set()
        
        if '*' in indexes:

            sel.update([at for at in self._universe.atomList()])
        
        else:
            vals = set([int(v) for v in indexes])
            sel.update([at for at in self._universe.atomList() if at.index in vals])
            
        return sel
        
class AtomPicked(AtomIndex):

    type = "atompicked"

    section = "miscellaneous"

class AtomName(Selector):

    type = "atomname"

    section = "atoms"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        self._choices.extend(sorted(set([at.name.strip().lower() for at in self._universe.atomList()])))


    def select(self, types):
        '''
        Returns the atoms that matches a given list of atom types.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the atom types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([v.lower() for v in types])
            sel.update([at for at in self._universe.atomList() if at.name.strip().lower() in vals])
        
        return sel

class AtomSymbol(Selector):

    type = "atomsymbol"

    section = "atoms"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        self._choices.extend(sorted(set([at.symbol.strip().lower() for at in self._universe.atomList()])))


    def select(self, types):
        '''
        Returns the atoms that matches a given list of atom types.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the atom types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([v.lower() for v in types])
            sel.update([at for at in self._universe.atomList() if at.symbol.strip().lower() in vals])
        
        return sel

class Backbone(Selector):

    type = "backbone"

    section = "biopolymers"

    def select(self, *args):
        '''
        Returns the backbone atoms.
        
        Only for Protein, PeptideChain and NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()

        for obj in self._universe.objectList():
            try:
                sel.update([at for at in obj.backbone().atomList()])
            except AttributeError:
                pass
            
        return sel

class Bases(Selector):

    type = "bases"

    section = "nucleic acids"

    def select(self, *args):
        '''
        Returns the bases atoms.
        
        Only for NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():
            try:
                sel.update([at for at in obj.bases().atomList()])
            except AttributeError:
                pass
            
        return sel
       

class C_Alphas(Selector):

    type = "c_alphas"

    section = "proteins"

    def select(self, *args):
        '''
        Returns the c_alpha atoms.
        
        Only for Protein and PeptideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()
        
        for obj in self._universe.objectList():            
            try:            
                sel.update([at for at in obj.atomList() if at.name.strip().lower() == 'c_alpha'])
            except AttributeError:
                pass

        return sel

class ChainName(Selector):

    type = "chainname"

    section = "proteins"

    def __init__(self, universe):
        
        Selector.__init__(self,universe)
                
        for obj in self._universe.objectList():
            if isinstance(obj, (PeptideChain, Protein)):
                self._choices.extend([c.name for c in obj])
        

    def select(self, names):
        '''
        Returns the atoms that matches a given list of chain names.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the chain names list.
        @type names: list
        '''
        
        sel = set()

        if '*' in names:
            for obj in self._universe.objectList():
                try:
                    sel.update([at for at in obj.atomList()])
                except AttributeError:
                    pass
        
        else:
            
            vals = set([v.lower() for v in names])
    
            for obj in self._universe.objectList():
                try:
                    for chain in obj:
                        chainName = chain.name.strip().lower()
                        if chainName in vals: 
                            sel.update([at for at in chain.atomList()])
                except AttributeError:
                    pass
                
        return sel
    
class HydrogenBoundToCarbon(Selector):
    
    type = "C-H"
    
    section = "hydrogens"

    def select(self, *args):

        sel = set()
            
        for obj in self._universe.objectList():
                                        
            carbons = [at for at in obj.atomList() if at.type.name.strip().lower() == 'carbon']
            
            for car in carbons:
                neighbours = car.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                sel.update(hydrogens)
                    
        return sel

class HydrogenBoundToHeteroatom(Selector):
    
    type = "X-H"
    
    section = "hydrogens"

    def select(self, *args):

        sel = set()
            
        for obj in self._universe.objectList():
                                        
            heteroatoms = [at for at in obj.atomList() if at.type.name.strip().lower() not in ['carbon','hydrogen']]
            
            for het in heteroatoms:
                neighbours = het.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                sel.update(hydrogens)
                    
        return sel

class HydrogenBoundToNitrogen(Selector):
    
    type = "N-H"
    
    section = "hydrogens"

    def select(self, *args):

        sel = set()
            
        for obj in self._universe.objectList():
                                        
            nitrogens = [at for at in obj.atomList() if at.type.name.strip().lower() == 'nitrogen']
            
            for nit in nitrogens:
                neighbours = nit.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                sel.update(hydrogens)
                    
        return sel

class HydrogenBoundToOxygen(Selector):
    
    type = "O-H"
    
    section = "hydrogens"

    def select(self, *args):

        sel = set()
            
        for obj in self._universe.objectList():
                                        
            oxygens = [at for at in obj.atomList() if at.type.name.strip().lower() == 'oxygen']
            
            for oxy in oxygens:
                neighbours = oxy.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                sel.update(hydrogens)
                    
        return sel
       
class Hydroxyl(Selector):

    type = "hydroxyl"

    section = "chemical groups"

    def select(self, *args):
        '''
         Returns the hydroxyl atoms.

         @param universe: the universe
         @type universe: MMTK.universe
         '''
        
        sel = set()

        for obj in self._universe.objectList():            
            oxygens = [at for at in obj.atomList() if at.type.name.strip().lower() == 'oxygen']
            for oxy in oxygens:
                neighbours = oxy.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                if len(hydrogens) == 1:
                    sel.update([oxy] + hydrogens)
  
        return sel

class Macromolecule(Selector):
    
    type = "macromolecule"
    
    section = "miscellaneous"
    
    lookup = {NucleotideChain:"nucleotide_chain",PeptideChain:"peptide_chain",Protein:"protein"}

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        self._choices.extend(["peptide_chain","protein","nucleotide_chain"])
         
    def select(self, macromolecules):
        '''
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param classes: the residue classes list.
        @type classes: list
        '''
                                
        sel = set()

        if '*' in macromolecules:
            for obj in self._universe.objectList():
                if isinstance(obj, (NucleotideChain,PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:
            for obj in self._universe.objectList():
                m = Macromolecule.lookup.get(obj.__class__,None)
                if m in macromolecules:
                    sel.update([at for at in obj.atomList()])

        return sel

class Methyl(Selector):

    type = "methyl"

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the methyl atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():
            carbons = [at for at in obj.atomList() if at.type.name.strip().lower() == 'carbon']
            for car in carbons:
                neighbours = car.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                if len(hydrogens) == 3:
                    sel.update([car] + hydrogens)

        return sel

class MolIndex(Selector):

    type = "molindex"

    section = "molecules"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        self._choices.extend(range(len(self._universe.objectList())))    

    def select(self, values):
        '''
        Returns the atoms that matches a given list of molecule indexes.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param indexes: the molecule indexes list.
        @type indexes: list
        '''
        
        sel = set()

        if '*' in values:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([int(v) for v in values])

            objList = self._universe.objectList()
        
            sel.update([at for v in vals for at in objList[v].atomList()])
        
        return sel

class MolName(Selector):

    type = "molname"

    section = "molecules"

    def __init__(self, universe):

        Selector.__init__(self,universe)
        
        self._choices.extend(sorted(set([obj.name for obj in self._universe.objectList()])))


    def select(self, names):
        '''
        Returns the atoms that matches a given list of molecule names.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the molecule names list.
        @type names: list
        '''
        
        sel = set()
        
        if '*' in names:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([v.lower() for v in names])

            for obj in self._universe.objectList():
                try:
                    if obj.name.strip().lower() in vals:
                        sel.update([at for at in obj.atomList()])
                except AttributeError:
                    pass
                
        return sel
    
class NuclName(Selector):

    type = "nuclname"

    section = "nucleic acids"

    def __init__(self, universe):

        Selector.__init__(self,universe)

        for obj in self._universe.objectList():
            if isinstance(obj, NucleotideChain):
                self._choices.extend([r.fullName() for r in obj.residues()])
        

    def select(self, names):
        '''
        Returns the atoms that matches a given list of nucleotide names.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the nucletodide names list.
        @type names: list
        '''
        
        sel = set()

        if '*' in names:
            for obj in self._universe.objectList():
                if isinstance(obj, NucleotideChain):
                    sel.update([at for at in obj.atomList()])
        
        else:
            vals = set([v.lower() for v in names])

            for obj in self._universe.objectList():
                try:
                    res = obj.residues()
                    for nucl in res:
                        nuclName = nucl.fullName().strip().lower()
                        if nuclName in vals:
                            sel.update([at for at in nucl.atomList()])
                except AttributeError:
                    pass
                       
        return sel
                                         
class NuclType(Selector):

    type = "nucltype"

    section = "nucleic acids"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        for obj in self._universe.objectList():
            if isinstance(obj, NucleotideChain):
                self._choices.extend([r.symbol.strip().lower() for r in obj.residues()])
                

    def select(self, types):
        '''
        Returns the atoms that matches a given list of nucleotide types.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the nucleotide types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:
            for obj in self._universe.objectList():
                if isinstance(obj, NucleotideChain):
                    sel.update([at for at in obj.atomList()])
        
        else:
            vals = set([v.lower() for v in types])

            for obj in self._universe.objectList():
                try:
                    res = obj.residues()
                    for nucl in res:
                        nuclType = nucl.symbol.strip().lower()
                        if nuclType in vals:
                            sel.update([at for at in nucl.atomList()])
                except AttributeError:
                    pass
                
        return sel
                    
class PDBFile(Selector):

    type = "pdbfile"

    section = None

    def select(self, filename):
        '''
        Returns the atoms tagged in a given PDB file.

        @param universe: the universe
        @type universe: MMTK.universe
    
        @param filename: the PDB file.
        @type filename: string
        '''
        
        if not isinstance(filename,basestring):
            raise SelectorError("Invalid type for PDB filename %r" % filename)
                
        sel = set()
        
        # Check that the PDB file exists.
        filename = PLATFORM.get_path(filename)
        if os.path.exists(filename):

            # Try to open it as a PDB file. Otherwise throw an error.
            try:
                pdbConf = PDBConfiguration(filename)
            except:
                pass
            else:
                # Will contain the PDB positions of the atoms marked for selection. 
                pdbSelection = []
    
                # Loop over the atoms of the PDB file to get the atoms whose occupancy is set to 1.00.
                for res in pdbConf.residues:
                    for at in res:
                        if at.properties['occupancy'] == 1.0:
                            pdbSelection.append(tuple([at.position]))

                # A dictionnary whose key,value are respectively the position of the atoms of the universe and their index.
                univCoord = {}
                for at in self._universe.atomList():
                    univCoord[tuple([round(v, 4) for v in at.position()])] = at

                # Loop over the PDB atoms marked for selection.
                for p in pdbSelection:
                    # Add to the selection the index of the atom that matches this position.
                    if univCoord.has_key(p):
                        sel.update([univCoord[p]])
                        
        return sel
                                    
class Phosphate(Selector):

    type = "phosphate"

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the phosphate atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()

        for obj in self._universe.objectList():

            phosphorus = [at for at in obj.atomList() if at.type.name.strip().lower() == 'phosphorus']
            for pho in phosphorus:
                neighbours = pho.bondedTo()
                oxygens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'oxygen'] 
                if len(oxygens) == 4:
                    sel.update([pho] + oxygens)
                
        return sel
                
class PythonScript(Selector):
    
    type = "pythonscript"
    
    section = None

    def select(self, scripts):
        
        sel = set()
                                
        for s in scripts:
            
            namespace = {"universe" : self._universe}
        
            try:
                execfile(s,namespace)
            # Any kind of error that may occur in the script must be caught 
            except:
                continue
            else:
                if not namespace.has_key("selection"):
                    continue
                                
                sel.update(namespace["selection"])
                                        
        return sel
                                         
class ResClass(Selector):

    type = "resclass"

    section = "proteins"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                        
        self._choices.extend(sorted(CHEMFAMILIES.keys()))

    def select(self, classes):
        '''
        Returns the atoms that matches a given list of peptide classes.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param classes: the residue classes list.
        @type classes: list
        '''
                
        sel = set()

        if '*' in classes:
            for obj in self._universe.objectList():
                if isinstance(obj, (PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:        
            vals = set([v.lower() for v in classes])
        
            selRes = set()
            for v in vals:
                if CHEMFAMILIES.has_key(v):
                    selRes.update(CHEMFAMILIES[v])
                                                                                 
            for obj in self._universe.objectList():
                try:        
                    res = obj.residues()
                    for r in res:
                        resName = r.symbol.strip().lower()
                        if resName in selRes:
                            sel.update([at for at in r.atomList()])
                except AttributeError:
                    pass
                                                   
        return sel

class ResName(Selector):

    type = "resname"

    section = "proteins"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                
        for obj in self._universe.objectList():
            if isinstance(obj, (PeptideChain, Protein)):
                for chain in obj:
                    self._choices.extend([r.fullName() for r in chain.residues()])
                        
    def select(self, names):
        '''
        Returns the atoms that matches a given list of peptide names.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the residue names list.
        @type names: list
        '''
                        
        sel = set()

        if '*' in names:
            for obj in self._universe.objectList():
                if isinstance(obj, (PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:            
            vals = set([v.strip().lower() for v in names])

            for obj in self._universe.objectList():
                try:
                    for r in obj.residues():
                        resName = r.fullName().strip().lower()
                        if resName in vals: 
                            sel.update([at for at in r.atomList()])
                except:
                    pass
                
        return sel
        
class ResType(Selector):

    type = "restype"

    section = "proteins"

    def __init__(self, universe):

        Selector.__init__(self,universe)
                                
        for obj in self._universe.objectList():
            if isinstance(obj, (PeptideChain, Protein)):
                self._choices.extend([r.symbol.strip().lower() for r in obj.residues()])
                

    def select(self, types):
        '''
        Returns the atoms that matches a given list of peptide types.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the residue types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:
            for obj in self._universe.objectList():
                if isinstance(obj, (PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:                
            vals = set([v.strip().lower() for v in types])

            for obj in self._universe.objectList():
                try:
                    for r in obj.residues():
                        resType = r.symbol.strip().lower()
                        if resType in vals:
                            sel.update([at for at in r.atomList()])
                except AttributeError:
                    pass
                
        return sel          
    
class SideChains(Selector):

    type = "sidechains"

    section = "biopolymers"

    def select(self, *args):
        '''
        Returns the sidechains atoms.
    
        Only for Protein, PeptideChain and NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()
    
        for obj in self._universe.objectList():
            try:
                sel.update([at for at in obj.sidechains().atomList()])
            except AttributeError:
                pass
        
        return sel
        
class Sulphate(Selector):

    type = "sulphate"

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the sulphate atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()

        for obj in self._universe.objectList():

            sulphurs = [at for at in obj.atomList() if at.type.name.strip().lower() in ['sulphur', 'sulfur']]
            for sul in sulphurs:
                neighbours = sul.bondedTo()
                oxygens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'oxygen'] 
                if len(oxygens) == 4:
                    sel.update([sul] + oxygens)
                
        return sel
    
class Thiol(Selector):

    type = "thiol"

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the thiol atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():

            sulphurs = [at for at in obj.atomList() if at.type.name.strip().lower() in ['sulphur', 'sulfur']]
            for sul in sulphurs:
                neighbours = sul.bondedTo()
                if not neighbours:
                    neighbours = self._universe.selectShell(sul,r1=0.0,r2=0.11)
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen'] 
                if len(hydrogens)==1:
                    sel.update([sul] + hydrogens)
                
        return sel
               
class Within(Selector):

    type = "within"

    section = None

    def select(self, atoms, mini=0.0, maxi=1.0):

        sel = set()

        for at in atoms:
            sel.update([a for a in self._universe.selectShell(at.position(),mini,maxi).atomList()])
        
        return sel

class Expression(Selector):

    type = "expression"

    section = None

    def select(self, expression):
                   
        sel = set()
                        
        expression = expression.lower()
        
        aList = self._universe.atomList()
                
        _,_,_ = self._universe.configuration().array.T
                                
        sel.update([aList[idx] for idx in eval(expression)])
        
        return sel
