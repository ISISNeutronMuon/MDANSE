from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
               
class Expression(ISelector):

    section = None

    def select(self, expression):
                   
        sel = set()
                        
        expression = expression.lower()
        
        aList = self._universe.atomList()
                
        _,_,_ = self._universe.configuration().array.T
                                
        sel.update([aList[idx] for idx in eval(expression)])
        
        return sel

REGISTRY["expression"] = Expression
