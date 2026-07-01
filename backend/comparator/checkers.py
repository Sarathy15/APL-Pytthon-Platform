import numpy as np

class NanChecker:
    @staticmethod
    def check(a, b):
        # Strict checking for NaN propagation in finance data
        return np.all(np.isnan(a) == np.isnan(b))

class ShapeChecker:
    @staticmethod
    def check(a, b):
        return np.shape(a) == np.shape(b)

class ToleranceChecker:
    @staticmethod
    def check(a, b, atol=1e-8):
        return np.allclose(a, b, atol=atol)
