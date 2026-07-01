import numpy as np


class IndexChecker:
    @staticmethod
    def verify(a: np.ndarray, b: np.ndarray, apl_origin: int = 1) -> bool:
        try:
            if not isinstance(apl_origin, int) or apl_origin == 0:
                return True
            if a.shape != b.shape:
                return True
            if a.size == 0:
                return True
            if np.issubdtype(a.dtype, np.integer) and np.issubdtype(b.dtype, np.integer):
                if np.array_equal(a, b + 1) or np.array_equal(a, b - 1):
                    return False
            return True
        except Exception:
            return True
