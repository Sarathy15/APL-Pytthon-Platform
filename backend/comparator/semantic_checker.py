import numpy as np


class SemanticChecker:
    @staticmethod
    def verify(a: np.ndarray, b: np.ndarray, tol: float = 1e-7, allow_permutation: bool = False) -> bool:
        try:
            if a.shape != b.shape:
                return False
            if np.issubdtype(a.dtype, np.number) and np.issubdtype(b.dtype, np.number):
                return bool(np.allclose(a.astype(np.float64), b.astype(np.float64), rtol=tol, atol=tol, equal_nan=True))
            if allow_permutation and a.ndim == 1 and b.ndim == 1:
                return np.array_equal(np.sort(a), np.sort(b))
            return np.array_equal(a, b)
        except Exception:
            return False
