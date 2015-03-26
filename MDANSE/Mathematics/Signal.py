import math

import numpy

from MDANSE.Core.Error import Error

class SignalError(Error):
    pass

INTERPOLATION_ORDER = []

INTERPOLATION_ORDER.append(numpy.array([[-3., 4.,-1.],
                                        [-1., 0., 1.],
                                        [ 1.,-4., 3.]], dtype=numpy.float64))


INTERPOLATION_ORDER.append(numpy.array([[-3., 4.,-1.],
                                        [-1., 0., 1.],
                                        [ 1.,-4., 3.]], dtype=numpy.float64))

INTERPOLATION_ORDER.append(numpy.array([[-11., 18., -9., 2.],
                                        [ -2., -3.,  6.,-1.],
                                        [  1., -6.,  3., 2.],
                                        [ -2.,  9.,-18.,11.]], dtype=numpy.float64))

INTERPOLATION_ORDER.append(numpy.array([[-50., 96.,-72., 32.,-6.],
                                        [ -6.,-20., 36.,-12., 2.],
                                        [  2.,-16.,  0., 16.,-2.],
                                        [ -2., 12.,-36., 20., 6.],
                                        [  6.,-32., 72.,-96.,50.]], dtype=numpy.float64))

INTERPOLATION_ORDER.append(numpy.array([[-274., 600.,-600., 400.,-150., 24.],
                                        [ -24.,-130., 240.,-120.,  40., -6.],
                                        [   6., -60., -40., 120., -30.,  4.],
                                        [  -4.,  30.,-120.,  40.,  60., -6.],
                                        [   6., -40., 120.,-240., 130., 24.],
                                        [ -24., 150.,-400., 600.,-600.,274.]], dtype=numpy.float64))


def correlation(x, y=None, axis=0, sumOverAxis=None, average=None):
    """Returns the numerical correlation between two signals.

    @param inputSeries1: the first signal.
    @type inputSeries1: NumPy array   
    
    @param inputSeries2: if not None, the second signal otherwise the correlation will be an autocorrelation.
    @type inputSeries2: NumPy array or None
    
    @return: the result of the numerical correlation.
    @rtype: NumPy array

    @note: if |inputSeries1| is a multidimensional array the correlation calculation is performed on
    the first dimension.

    @note: The correlation is computed using the FCA algorithm.
    """
    
    x = numpy.array(x)
    
    n = x.shape[axis]
            
    X = numpy.fft.fft(x, 2*n,axis=axis)

    if y is not None:
        y = numpy.array(y)
        Y = numpy.fft.fft(y, 2*n,axis=axis)
    else:
        Y = X
    
    s = [slice(None)]*x.ndim

    s[axis] = slice(0,x.shape[axis],1)
    
    corr = numpy.real(numpy.fft.ifft(numpy.conjugate(X)*Y,axis=axis)[s])
            
    norm = n - numpy.arange(n)
        
    s = [numpy.newaxis]*x.ndim
    s[axis] = slice(None)
        
    corr = corr/norm[s]
                    
    if sumOverAxis is not None:
        corr = numpy.sum(corr,axis=sumOverAxis)
    elif average is not None:
        corr = numpy.average(corr,axis=average)
            
    return corr

def normalize(x, axis=0):

    s = [slice(None)]*x.ndim
    s[axis] = slice(0,1,1)
    
    nx = x/x[s]
    return nx
    

def differentiate(a, dt=1.0, order=0):
        
    try:
        coefs = INTERPOLATION_ORDER[order]
    except TypeError:
        raise SignalError("Invalid type for differentiation order")
    except IndexError:
        raise SignalError("Invalid differentiation order")
        
    # outputSeries is the output resulting from the differentiation
    ts = numpy.zeros(a.shape, dtype=numpy.float)
        
    if order == 0:
                        
        ts[0] = numpy.add.reduce(coefs[0,:]*a[:3])
        ts[-1] = numpy.add.reduce(coefs[2,:]*a[-3:])

        gj = a[1:] - a[:-1]
        ts[1:-1] = (gj[1:]+gj[:-1])

    # Case of the order 2
    elif order == 1:

        ts[0]  = numpy.add.reduce(coefs[0,:]*a[:3])
        ts[-1] = numpy.add.reduce(coefs[2,:]*a[-3:])

        gj      = numpy.zeros((a.size-2,3), dtype=numpy.float)
        gj[:,0] = coefs[1,0]*a[:-2]
        gj[:,1] = coefs[1,1]*a[1:-1]
        gj[:,2] = coefs[1,2]*a[2:]
        ts[1:-1] = numpy.add.reduce(gj,-1)

    # Case of the order 3
    elif order == 2:

        # Special case for the first and last elements
        ts[0]  = numpy.add.reduce(coefs[0,:]*a[:4])
        ts[1]  = numpy.add.reduce(coefs[1,:]*a[:4])
        ts[-1] = numpy.add.reduce(coefs[3,:]*a[-4:])

        # General case
        gj      = numpy.zeros((a.size-3,4), dtype=numpy.float)
        gj[:,0] = coefs[2,0]*a[:-3]
        gj[:,1] = coefs[2,1]*a[1:-2]
        gj[:,2] = coefs[2,2]*a[2:-1]
        gj[:,3] = coefs[2,3]*a[3:]
        ts[2:-1] = numpy.add.reduce(gj,-1)

    # Case of the order 4
    elif order == 3:

        # Special case for the first and last elements
        ts[0]  = numpy.add.reduce(coefs[0,:]*a[:5])
        ts[1]  = numpy.add.reduce(coefs[1,:]*a[:5])
        ts[-2] = numpy.add.reduce(coefs[3,:]*a[-5:])
        ts[-1] = numpy.add.reduce(coefs[4,:]*a[-5:])

        # General case
        gj      = numpy.zeros((a.size-4,5), dtype=numpy.float)
        gj[:,0] = coefs[2,0]*a[:-4]
        gj[:,1] = coefs[2,1]*a[1:-3]
        gj[:,2] = coefs[2,2]*a[2:-2]
        gj[:,3] = coefs[2,3]*a[3:-1]
        gj[:,4] = coefs[2,4]*a[4:]
        ts[2:-2] = numpy.add.reduce(gj,-1)

    # Case of the order 5
    elif order == 4:

        # Special case for the first and last elements
        ts[0]  = numpy.add.reduce(coefs[0,:]*a[:6])
        ts[1]  = numpy.add.reduce(coefs[1,:]*a[:6])
        ts[2]  = numpy.add.reduce(coefs[2,:]*a[:6])
        ts[-2] = numpy.add.reduce(coefs[4,:]*a[-6:])
        ts[-1] = numpy.add.reduce(coefs[5,:]*a[-6:])

        # General case
        gj      = numpy.zeros((a.size-5,6), dtype=numpy.float)
        gj[:,0] = coefs[3,0]*a[:-5]
        gj[:,1] = coefs[3,1]*a[1:-4]
        gj[:,2] = coefs[3,2]*a[2:-3]
        gj[:,3] = coefs[3,3]*a[3:-2]
        gj[:,4] = coefs[3,4]*a[4:-1]
        gj[:,5] = coefs[3,5]*a[5:]
        ts[3:-2] = numpy.add.reduce(gj,-1)


    fact = 1.0/(dt*math.factorial(max(order+1,2)))
    
    ts *= fact
        
    return ts        

def symmetrize(signal, axis=0):
    """Return a symmetrized version of an input signal

    :Parameters:
        #. signal (numpy.array): the input signal
        #. axis (int): the axis along which the signal should be symmetrized
    :Returns:
        #. numpy.array: the symmetrized signal
    """
    
    s = [slice(None)]*signal.ndim
    s[axis] = slice(-1,0,-1)
            
    signal = numpy.concatenate((signal[s],signal),axis=axis)
    
    return signal

def get_spectrum(signal,window=None,timeStep=1.0,axis=0):
                            
    signal = symmetrize(signal,axis)

    if window is None:
        window = numpy.ones(signal.shape[axis])

    s = [numpy.newaxis]*signal.ndim
    s[axis] = slice(None)
    
    return numpy.fft.fftshift(numpy.abs(numpy.fft.fft(signal*window[s],axis=axis)),axes=axis)*timeStep    
    
    
