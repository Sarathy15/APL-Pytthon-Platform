import numpy as np


class NanChecker:
    @staticmethod
    def verify(a: np.ndarray, b: np.ndarray) -> bool:
        try:
            if a.shape != b.shape:
                return False
            if a.size == 0:
                return True
            a_nan = np.isnan(a, where=np.ones(a.shape, dtype=bool)) if np.issubdtype(a.dtype, np.number) else np.zeros(a.shape, dtype=bool)
            b_nan = np.isnan(b, where=np.ones(b.shape, dtype=bool)) if np.issubdtype(b.dtype, np.number) else np.zeros(b.shape, dtype=bool)
            return np.array_equal(a_nan, b_nan)
        except Exception:
            try:
                a_list = np.asarray(a).flatten().tolist()
                b_list = np.asarray(b).flatten().tolist()
                return [isinstance(x, float) and np.isnan(x) for x in a_list] == [isinstance(x, float) and np.isnan(x) for x in b_list]
            except Exception:
                return False
