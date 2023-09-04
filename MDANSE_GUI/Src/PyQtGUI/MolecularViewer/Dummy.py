import numpy as np


class PyConnectivity:
    """At the moment MDANSE_GUI does not contain any checks for connectivity.
    The intended solution is to include a connectivity scanner in the
    trajectory converter.
    In the meantime, since the MolecularViewer expects a PyConnectivity object,
    this dummy has been created. It never finds any bonds.
    """

    def __init__(self, *args, **kwargs):
        pass

    def add_point(self, index: int, point: np.ndarray, radius: float) -> bool:
        return True

    def find_collisions(self, tolerance: float) -> dict:
        return {}

    def get_neighbour(self, point: np.ndarray) -> int:
        return 0
