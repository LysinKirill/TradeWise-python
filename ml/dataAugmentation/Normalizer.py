import numpy as np


class Normalizer:
    def __init__(self,
                 mins: np.ndarray | None = None,
                 maxs: np.ndarray | None = None):
        self.mins = mins
        self.maxs = maxs

    def fit_transform(self, x):
        """Normalize multiple features to [-1, 1] range"""
        self.mins = np.min(x, axis=0)
        self.maxs = np.max(x, axis=0)
        normalized_x = 2 * (x - self.mins) / (self.maxs - self.mins) - 1
        return normalized_x

    def transform(self, x):
        return 2 * (x - self.mins) / (self.maxs - self.mins) - 1

    def inverse_transform(self, x):
        return (x + 1) / 2 * (self.maxs - self.mins) + self.mins