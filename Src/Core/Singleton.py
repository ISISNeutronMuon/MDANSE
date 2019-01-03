class Singleton(type):
    '''
    Metaclass that implements the singleton pattern.
    '''

    __instances = {}
    
    def __call__(self, *args, **kwargs):
        '''
        Creates (or returns if it has already been instanciated) an instance of the class.
        '''
    
        if self.__name__ not in self.__instances:
            self.__instances[self.__name__] = super(Singleton, self).__call__(*args, **kwargs)
            
        return self.__instances[self.__name__]
