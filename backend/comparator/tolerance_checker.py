import numpy as np


class ToleranceChecker:
    @staticmethod
    def verify(a: np.ndarray, b: np.ndarray, rtol: float = 1e-7, atol: float = 1e-9) -> bool:
        try:
            if a.shape != b.shape:
                return False
            if np.issubdtype(a.dtype, np.number) and np.issubdtype(b.dtype, np.number):
                return bool(np.allclose(a.astype(np.float64), b.astype(np.float64), rtol=rtol, atol=atol, equal_nan=True))
            return np.array_equal(a, b)
        except Exception:
            return False
