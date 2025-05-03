import numpy as np


class Normalizer:
    def __init__(
        self,
        min_val: float | None = None,
        max_val: float | None = None
    ):
        self.min = min_val
        self.max = max_val

    def fit_transform(self, x):
        self.min = np.min(x, axis=0)[0]
        self.max = np.max(x, axis=0)[0]
        normalized_x = 2 * (x - self.min) / (self.max - self.min) - 1
        return normalized_x

    def transform(self, x):
        normalized_x = 2 * (x - self.min) / (self.max - self.min) - 1
        return normalized_x

    def inverse_transform(self, x):
        original_x = (x + 1) / 2 * (self.max - self.min) + self.min
        return original_x