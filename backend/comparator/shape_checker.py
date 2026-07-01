import numpy as np


class ShapeChecker:
    @staticmethod
    def verify(a: np.ndarray, b: np.ndarray) -> bool:
        try:
            return a.shape == b.shape
        except Exception:
            return False
