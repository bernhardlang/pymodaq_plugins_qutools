import numpy as np
import random
import matplotlib.pyplot as plt
from pymodaq_plugins_qutools.histogram import Histogram


def next_event(t, rate):
    return t - np.log(1.0 - random.random()) / rate

rate = 1e4
counts = []
events = []
t = 0
for i in range(1,100):
    count = 0
    t = next_event(t, rate)
    while t < i:
        count += 1
        events.append(t)
        t = next_event(t, rate)
    counts.append(count)

plt.plot(counts)
plt.show()

channels = [1 for _ in range(len(events))]

triggers = []
t = next_event(0, 1e3)
while t < 100:
    triggers.append(t)
    t = next_event(t, 1e3)
triggers = [1e-3 * i for i in range(1,100000)]

channels += [0 for _ in range(len(triggers))]
events += triggers
events = list(zip(events, channels))
events.sort()
timestamps, channels = list(zip(*events))
timestamps, channels = list(timestamps), list(channels)

last_trigger = 0
events = []
for i,timestamp in enumerate(timestamps):
    if channels[i]:
        events.append(timestamp - last_trigger)
    else:
        last_trigger = timestamp

hist = Histogram(100, events)
plt.plot(hist.bins)
plt.show()
