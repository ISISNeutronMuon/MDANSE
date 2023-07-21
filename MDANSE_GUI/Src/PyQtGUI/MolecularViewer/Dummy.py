
import numpy as np


class PyConnectivity:

    def __init__(self, *args, **kwargs):
        pass

    def add_point(self, index: int, point: np.ndarray, radius: float) -> bool:
        return True

    def find_collisions(self, tolerance: float) -> dict:
        return {}

    def get_neighbour(self, point: np.ndarray) -> int:
        return 0
