import numpy as np

from MMTK import Atom
from MMTK.ParticleProperties import Configuration
from MMTK.Universe import ParallelepipedicPeriodicUniverse

np.random.seed(1)

n_atoms = 5

u = ParallelepipedicPeriodicUniverse()

for i in range(n_atoms):
    u.addObject(Atom('H'))
    
uc = np.array([[1.0,2.0,3.0],[2.0,-1.0,3.0],[1.0,1.0,1.0]])
#uc = np.array([[10.0,0.0,0.0],[0.0,10.0,0.0],[0.0,0.0,10.0]])
u.setShape(uc)

coords = np.random.uniform(-10,10,(n_atoms,3))
conf = Configuration(u,coords)
u.setConfiguration(conf)

print(u.configuration().array)
u.foldCoordinatesIntoBox()
print(u.configuration().array)


