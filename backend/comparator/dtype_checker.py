import numpy as np


class DtypeChecker:
    @staticmethod
    def verify(a: np.ndarray, b: np.ndarray) -> bool:
        try:
            a_dtype = a.dtype
            b_dtype = b.dtype
            if a_dtype == b_dtype:
                return True
            if np.issubdtype(a_dtype, np.integer) and np.issubdtype(b_dtype, np.floating):
                return True
            if np.issubdtype(a_dtype, np.floating) and np.issubdtype(b_dtype, np.integer):
                return True
            if np.issubdtype(a_dtype, np.bool_) and np.issubdtype(b_dtype, np.integer):
                return True
            return False
        except Exception:
            return False
