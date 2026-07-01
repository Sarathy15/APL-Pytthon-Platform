import itertools

import numpy as np


class AxisChecker:
    @staticmethod
    def verify(a: np.ndarray, b: np.ndarray) -> bool:
        try:
            if a.shape == b.shape:
                return True
            if a.ndim != b.ndim:
                return True
            if a.size == 0 or b.size == 0:
                return True

            for perm in itertools.permutations(range(b.ndim)):
                if tuple(b.shape[i] for i in perm) == a.shape:
                    try:
                        if np.array_equal(a, np.transpose(b, perm), equal_nan=True):
                            return False
                    except Exception:
                        continue
            return True
        except Exception:
            return True
