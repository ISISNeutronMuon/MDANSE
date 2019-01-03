from MDANSE.Framework.Jobs.IJob import IJob

class Converter(IJob):
    
    category = ('Converters',)
    
    ancestor = ['empty_data']
