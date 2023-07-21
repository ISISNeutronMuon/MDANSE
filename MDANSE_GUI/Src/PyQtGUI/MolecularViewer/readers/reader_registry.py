# This dict will store a map between a filename extension and the actual reader corresponding to that file extension
REGISTERED_READERS = {}

def register_reader(typ):
    def decorator_register(cls):
        REGISTERED_READERS[typ] = cls 
        return cls
    return decorator_register
