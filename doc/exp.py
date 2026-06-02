import numpy as np
import matplotlib.pyplot as plt
from pymodaq_plugins_qutools.histogram import Histogram

X = [np.random.exponential(1) for _ in range(100000)]
hist = Histogram(100, X)
plt.plot(hist.centers, hist.bins)
plt.yscale('log')
plt.show()
