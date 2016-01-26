import numpy

from MDANSE.Core.Error import Error

class SignalError(Error):
    pass

INTERPOLATION_ORDER = {}

INTERPOLATION_ORDER["1st order"] = numpy.array([[-3., 4.,-1.],
                                                [-1., 0., 1.],
                                                [ 1.,-4., 3.]], dtype=numpy.float64)


INTERPOLATION_ORDER["2nd order"] = numpy.array([[-3., 4.,-1.],
                                                [-1., 0., 1.],
                                                [ 1.,-4., 3.]], dtype=numpy.float64)

INTERPOLATION_ORDER["3rd order"] = numpy.array([[-11., 18., -9., 2.],
                                                [ -2., -3.,  6.,-1.],
                                                [  1., -6.,  3., 2.],
                                                [ -2.,  9.,-18.,11.]], dtype=numpy.float64)

INTERPOLATION_ORDER["4th order"] = numpy.array([[-50., 96.,-72., 32.,-6.],
                                                [ -6.,-20., 36.,-12., 2.],
                                                [  2.,-16.,  0., 16.,-2.],
                                                [ -2., 12.,-36., 20., 6.],
                                                [  6.,-32., 72.,-96.,50.]], dtype=numpy.float64)

INTERPOLATION_ORDER["5th order"] = numpy.array([[-274., 600.,-600., 400.,-150., 24.],
                                                [ -24.,-130., 240.,-120.,  40., -6.],
                                                [   6., -60., -40., 120., -30.,  4.],
                                                [  -4.,  30.,-120.,  40.,  60., -6.],
                                                [   6., -40., 120.,-240., 130., 24.],
                                                [ -24., 150.,-400., 600.,-600.,274.]], dtype=numpy.float64)


def correlation(x, y=None, axis=0, sumOverAxis=None, average=None):
    """Returns the numerical correlation between two signals.

    :param x: the first signal.
    :type x: NumPy array   
    
    :param y: if not None, the correlation is performed between `x` and `y`. If None, the autocorrelation of `x` will be computed.
    :type y: NumPy array or None

    :param axis: the axis along which the correlation will be computed.
    :type axis: int

    :param sumOverAxis: if not None, the computed correlations will be sum over a given axis.
    :type sumOverAxis: int or None

    :param average: if not None, the computed correlations will be averaged over a given axis.
    :type average: int or None
    
    :return: the result of the numerical correlation.
    :rtype: NumPy array

    :note: The correlation is computed using the FCA algorithm.
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
    

def differentiate(a, dt=1.0, order="1st order"):
        
    if not INTERPOLATION_ORDER.has_key(order):
        raise SignalError("Invalid differentiation order")
        
    coefs = INTERPOLATION_ORDER[order]
        
    # outputSeries is the output resulting from the differentiation
    ts = numpy.zeros(a.shape, dtype=numpy.float)
    
    fact = 1.0/dt
        
    if order == "1st order":
                        
        ts[0] = numpy.add.reduce(coefs[0,:]*a[:3])
        ts[-1] = numpy.add.reduce(coefs[2,:]*a[-3:])

        gj = a[1:] - a[:-1]
        ts[1:-1] = (gj[1:]+gj[:-1])

        fact /= 2.0

    # Case of the order 2
    elif order == "2nd order":

        ts[0]  = numpy.add.reduce(coefs[0,:]*a[:3])
        ts[-1] = numpy.add.reduce(coefs[2,:]*a[-3:])

        gj      = numpy.zeros((a.size-2,3), dtype=numpy.float)
        gj[:,0] = coefs[1,0]*a[:-2]
        gj[:,1] = coefs[1,1]*a[1:-1]
        gj[:,2] = coefs[1,2]*a[2:]
        ts[1:-1] = numpy.add.reduce(gj,-1)

        fact /= 2.0

    # Case of the order 3
    elif order == "3rd order":

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

        fact /= 6.0

    # Case of the order 4
    elif order == "4th order":

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

        fact /= 24.0

    # Case of the order 5
    elif order == "5th order":

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

        fact /= 120.0

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

    window /= window[len(window)/2]

    s = [numpy.newaxis]*signal.ndim
    s[axis] = slice(None)

    # We compute the unitary inverse fourier transform with angular frequencies as described in
    # https://en.wikipedia.org/wiki/Fourier_transform#Discrete_Fourier_Transforms_and_Fast_Fourier_Transforms
    
    # For information about the manipulation around fftshift and ifftshift
    # http://www.mathworks.com/matlabcentral/newsreader/view_thread/285244
    
    fftSignal = 0.5*numpy.fft.fftshift(numpy.fft.fft(numpy.fft.ifftshift(signal*window[s],axes=axis),axis=axis),axes=axis)*timeStep/numpy.pi
    return fftSignal.real
    
    
