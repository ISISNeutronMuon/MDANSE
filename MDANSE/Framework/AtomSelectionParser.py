#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 27, 2015

:author: Eric C. Pellegrini
'''

import operator

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Externals.pyparsing.pyparsing import delimitedList, oneOf, opAssoc, operatorPrecedence, printables, Forward, OneOrMore, Optional, Word

class AtomSelectionParserError(Error):
    pass

class AtomSelectionParser(object):
        
    def __init__(self, universe):
        
        self._universe = universe
                
    def operator_and(self, token):
        
        token[0][1] = "&"
        
        return " ".join(token[0])

    def operator_not(self, token):
                                
        return 'REGISTRY[%r]["all"](universe).select() - %s' % ("selector",token[0][1])

    def operator_or(self, token):
        
        token[0][1] = "|"
            
        return " ".join(token[0])
    
    def parse_arguments(self,token):

        return "(%s) " % str(token)

    def parse_expression(self, token):
                        
        return "".join([str(t) for t in token])
    
    def parse_keyword(self, token):
                            
        return 'REGISTRY[%r]["%s"](universe).select' % ("selector",token[0])
    
    def parse_selection_expression(self, expression):
                
        expression = expression.replace("(","( ")
        expression = expression.replace(")"," )")
        
        linkers   = oneOf(["and","&","or","|","not","~"], caseless=True)
        keyword   = oneOf(REGISTRY["selector"].keys(), caseless=True).setParseAction(self.parse_keyword)
        arguments = Optional(~linkers + delimitedList(Word(printables,excludeChars=","),combine=False)).setParseAction(self.parse_arguments)
        
        selector = OneOrMore((keyword+arguments))
        
        grammar = Forward()
        
        grammar << selector.setParseAction(self.parse_expression)
        
        print "bef ", grammar.transformString(expression)

        grammar = operatorPrecedence(grammar, [(oneOf(["and","&"],caseless=True), 2, opAssoc.RIGHT , self.operator_and),
                                               (oneOf(["not","~"],caseless=True), 1, opAssoc.RIGHT, self.operator_not),
                                               (oneOf(["or","|"] ,caseless=True), 2, opAssoc.RIGHT , self.operator_or)],
                                     lpar="(",
                                     rpar=")")

        try:          
            parsedExpression = grammar.transformString(expression)
            namespace={"REGISTRY":REGISTRY,"universe":self._universe}
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
        
        print "parse_keyword"
                            
        return '"%s"(universe).select' % token[0]

    def parse_arguments(token):

        print "parse_arguments"

        return "(%s)" % str(token)

    def operator_and(token):

        print "operator_and"
        
        token[0][1] = "&"
        
        return " ".join(token[0])

    def operator_or(token):

        print "operator_or"
        
        token[0][1] = "|"
            
        return " ".join(token[0])

    def parse_expression(self, token):

        print "parse_expression"
                        
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
    
    print parsedExpression
