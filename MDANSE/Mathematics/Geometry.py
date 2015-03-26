import numpy

from Scientific.Geometry import Vector

def get_basis_vectors_from_cell_parameters(parameters):
    """Returns the basis vectors for the simulation cell from the six crystallographic parameters.
    
    @param parameters: the a, b, c, alpha, bete and gamma of the simulation cell.
    @type: parameters: list of 6 floats
    
    @return: a list of three Scientific.Geometry.Vector objects representing respectively a, b and c 
        basis vectors.
    @rtype: list
    """

    # The simulation cell parameters.
    a, b, c, alpha, beta, gamma = parameters
    
    # By construction the a vector is aligned with the x axis.
    e1 = Vector(a, 0.0, 0.0)

    # By construction the b vector is in the xy plane.
    e2 = b*Vector(numpy.cos(gamma), numpy.sin(gamma), 0.0)
    
    e3_x = numpy.cos(beta)
    e3_y = (numpy.cos(alpha) - numpy.cos(beta)*numpy.cos(gamma)) / numpy.sin(gamma)
    e3_z = numpy.sqrt(1.0 - e3_x**2 - e3_y**2)
    e3 = c*Vector(e3_x, e3_y, e3_z)

    return (e1, e2, e3)

        
def center_of_mass(coords, masses=None):
    """Computes the center of massfor a set of coordinates and masses 
    :Parameters:
        #. coords  ((n,3)-numpy.array): the input coordinates
        #. masses  ((n, )-numpy.array): the input masses
    :Returns:
        #. (3,)-numpy.array: the center of mass
    """
        
    return numpy.average(coords,weights=masses,axis=0)
    
center = center_of_mass
    
def build_cartesian_axes(origin, p1, p2, dtype = numpy.float64):
    
    origin = numpy.array(origin, dtype = dtype)
    p1 = numpy.array(p1, dtype = dtype)
    p2 = numpy.array(p2, dtype = dtype)
    
    
    v1 = p1 - origin
    v2 = p2 - origin
    
    n1 = (v1 + v2)
    n1 /= numpy.linalg.norm(n1)
    
    n3 = numpy.cross(v1,n1)
    n3 /= numpy.linalg.norm(n3)
    
    n2 = numpy.cross(n3,n1)
    n2 /= numpy.linalg.norm(n2)
    
    return n1,n2,n3
    
def generate_sphere_points(n):
    """Returns list of 3d coordinates of points on a sphere using the
    Golden Section Spiral algorithm.
    """
    
    points = []
    
    inc = numpy.pi * (3 - numpy.sqrt(5))
    
    offset = 2 / float(n)
    
    for k in range(int(n)):
        y = k * offset - 1 + (offset / 2)
        r = numpy.sqrt(1 - y*y)
        phi = k * inc
        points.append([numpy.cos(phi)*r, y, numpy.sin(phi)*r])
    
    return points    

def random_points_on_sphere(radius=1.0, nPoints=100):

    points = numpy.zeros((3,nPoints),dtype=numpy.float)
    
    theta = 2.0*numpy.pi*numpy.random.uniform(nPoints)
    u = numpy.random.uniform(-1.0,1.0,nPoints)
    points[0,:] = radius * numpy.sqrt(1 - u**2) * numpy.cos(theta)
    points[1,:] = radius * numpy.sqrt(1 - u**2) * numpy.sin(theta)
    points[2,:] = radius * u
    
    return points

def random_points_on_disk(axis, radius=1.0, nPoints=100):

    axis = Vector(axis).normal().array
    
    points = numpy.random.uniform(-radius,radius,3*nPoints)
    points = points.reshape((3,nPoints))

    proj = numpy.dot(axis,points)
    proj = numpy.dot(axis[:,numpy.newaxis],proj[numpy.newaxis,:])
    
    points -= proj
                        
    return points    

def random_points_on_circle(axis, radius=1.0, nPoints=100):

    axis = Vector(axis).normal().array
    
    points = numpy.random.uniform(-radius,radius,3*nPoints)
    points = points.reshape((3,nPoints))

    proj = numpy.dot(axis,points)
    proj = numpy.dot(axis[:,numpy.newaxis],proj[numpy.newaxis,:])
    
    points -= proj
    
    points *= (radius/numpy.sqrt(numpy.sum(points**2,axis=0)))
                        
    return points    



    
    
    
    