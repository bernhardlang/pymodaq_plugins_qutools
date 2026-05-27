import numpy as np


class Histogram:

    def __init__(self, n_bins, min_val=None, max_val=None):
        assert type(n_bins) == int
        self.n_bins = n_bins
        self._bins = None
        self._centers = None
        self._samples = 0
        self._normalised_bins = None
        self._mean = None
        self._sigma = None
        if isinstance(min_val, list) or isinstance(min_val, np.ndarray):
            self._set_up(min_val)
        elif min_val is not None:
            self.set_up(min_val, max_val)
            self._changed = False
            self.values = None
        else:
            self._changed = True

    def set_up(self, min_val, max_val):
        self._centers = np.linspace(min_val, max_val, self.n_bins)
        self.bin_width = self._centers[1] - self._centers[0]
        self.ranges = \
            np.linspace(min_val - self.bin_width, max_val + self.bin_width,
                        self.n_bins + 1)
        self._bins = np.zeros(self.n_bins)
        self.start_range = self.ranges[0]
        self._changed = True

    def _set_up(self, values):
        self.set_up(min(values), max(values))
        self.collect(values)

    def add(self, value):
        idx = int((value - self.start_range) / self.bin_width)
        if idx >= 0 and idx < self.n_bins:
        self._bins[idx] += 1

    def collect(self, values):
        for value in values:
            self.add(value)

    @property
    def bins(self):
        self._update()
        return self._bins

    @property
    def centers(self):
        self._update()
        return self._centers

    @property
    def samples(self):
        self._update()
        return self._samples

    @property
    def mean(self):
        self._update()
        return self._mean
    
    @property
    def sigma(self):
        self._update()
        return self._sigma

    @property
    def normalised_bins(self):
        self._update()
        return self._normalised_bins

    def _update(self):
        if not self._changed:
            return

        self._samples = sum(self._bins)
        self._normalised_bins = self._bins / (self._samples * self.bin_width)
        self._mean = \
            np.dot(self._normalised_bins, self._centers) * self.bin_width
        self._sigma = \
            np.sqrt(np.dot(self._normalised_bins,
                           (self._centers - self._mean)**2)
                    * self.bin_width)
        self._changed = False
