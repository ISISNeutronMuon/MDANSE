# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/AtomSelectionParser.py
# @brief     Implements module/class/test AtomSelectionParser
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import operator

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Externals.pyparsing.pyparsing import delimitedList, oneOf, opAssoc, operatorPrecedence, printables, Forward, OneOrMore, Optional, Word

class AtomSelectionParserError(Error):
    pass

class AtomSelectionParser(object):
        
    def __init__(self, chemicalSystem):
        
        self._chemicalSystem = chemicalSystem
                
    def operator_and(self, token):
        
        token[0][1] = "&"
        
        return " ".join(token[0])

    def operator_not(self, token):
                                
        return 'REGISTRY[%r]["all"](chemicalSystem).select() - %s' % ("selector",token[0][1])

    def operator_or(self, token):
        
        token[0][1] = "|"
            
        return " ".join(token[0])
    
    def parse_arguments(self,token):

        return "(%s) " % str(token)

    def parse_expression(self, token):
                        
        return "".join([str(t) for t in token])
    
    def parse_keyword(self, token):
                            
        return 'REGISTRY[%r]["%s"](chemicalSystem).select' % ("selector",token[0])
    
    def parse_selection_expression(self, expression):
                
        expression = expression.replace("(","( ")
        expression = expression.replace(")"," )")
        
        linkers   = oneOf(["and","&","or","|","not","~"], caseless=True)
        keyword   = oneOf(list(REGISTRY["selector"].keys()), caseless=True).setParseAction(self.parse_keyword)
        arguments = Optional(~linkers + delimitedList(Word(printables,excludeChars=","),combine=False)).setParseAction(self.parse_arguments)
        
        selector = OneOrMore((keyword+arguments))
        
        grammar = Forward()
        
        grammar << selector.setParseAction(self.parse_expression)
        
        grammar = operatorPrecedence(grammar, [(oneOf(["and","&"],caseless=True), 2, opAssoc.RIGHT , self.operator_and),
                                               (oneOf(["not","~"],caseless=True), 1, opAssoc.RIGHT, self.operator_not),
                                               (oneOf(["or","|"] ,caseless=True), 2, opAssoc.RIGHT , self.operator_or)],
                                     lpar="(",
                                     rpar=")")

        try:          
            parsedExpression = grammar.transformString(expression)
            namespace={"REGISTRY":REGISTRY,"chemicalSystem":self._chemicalSystem}
            selection = eval(parsedExpression,namespace)
        except:
            raise AtomSelectionParserError("%r is not a valid selection string expression" % expression)
        
        selection = sorted(selection, key=operator.attrgetter("index"))
                                
        return selection 
                                                                                                        
    def parse(self, expression):
                                    
        # Perfom the actual selection.
        selection = self.parse_selection_expression(expression)
                            
        if not selection:
            raise AtomSelectionParserError("No atoms matched the selection %r." % expression)
        
        indexes = [at.index for at in selection]
                
        return indexes
    
if __name__ == "__main__":

    from MDANSE.Externals.pyparsing.pyparsing import *

    def parse_keyword(token):
                                    
        return '"%s"(universe).select' % token[0]

    def parse_arguments(token):

        return "(%s)" % str(token)

    def operator_and(token):
        
        token[0][1] = "&"
        
        return " ".join(token[0])

    def operator_or(token):
        
        token[0][1] = "|"
            
        return " ".join(token[0])

    def parse_expression(self, token):
                        
        return "".join([str(t) for t in token])
        
    expression = 'carbo * or oxy * or nitro *'
    
    linkers   = oneOf(["and","or",], caseless=True)
    keyword   = oneOf(['carbo','oxy','nitro'], caseless=True).setParseAction(parse_keyword)
    arguments = Optional(~linkers + delimitedList(Word(printables,excludeChars=","),combine=False)).setParseAction(parse_arguments)
    
    selector = keyword+arguments
    
    grammar = Forward()
    
    grammar << selector.setParseAction(parse_expression)
    
    expr = operatorPrecedence(grammar, [(oneOf(["and"],caseless=True), 2, opAssoc.RIGHT , operator_and),
                                           (oneOf(["or"] ,caseless=True), 2, opAssoc.RIGHT , operator_or)],
                                 lpar="(",
                                 rpar=")")

    parsedExpression = expr.transformString(expression)

