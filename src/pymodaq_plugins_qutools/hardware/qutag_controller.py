import numpy as np
from threading import Thread
from pymodaq_plugins_qutools.hardware.QuTAG_HR import QuTAG

import time

def replace_char(string, pos, char):
    return string[:pos] + char + string[pos+1:]
# Could simply be string[pos] = char. However, in Python some features are
# simply broken by design :-/

class QuTAGController:

    SCOND_LVTTL = 1
    SCOND_NIM   = 2
    SCOND_MISC  = 3
     
    def __init__(self):
        self.initialised = False
        self.thread = None
        self.callback = None
        self.get_count_rate = np.zeros(8, dtype=np.int32)
        self.sample_count = np.zeros(8, dtype=np.int32)

    def __del__(self):
        if self.thread is not None:
            self.stop()
        if self.initialised:
            self.qutag.deInitialize()

    def open_communication(self, update_interval):
        try:
            self.qutag = QuTAG()
        except:
            raise RuntimeError("Couldn't initialise QuTAG")
        self.update_interval = update_interval
        self.initialised = True

    def close_communication(self):
        if self.initialised:
            self.qutag.deInitialize()
            self.initialised = False

    def set_update_interval(self, interval):
        self.update_interval = interval

    def is_initialised(self):
        return self.initialised

    def get_enabled_channels(self):
        start_enabled, enabled_channels = self.qutag.getChannelsEnabled()
        while len(enabled_channels) < 8:
            enabled_channels = '0' + enabled_channels
        return start_enabled, enabled_channels

    def get_enabled(self, channel):
        start_enabled, enabled_channels = self.get_enabled_channels()
        if channel:
            return enabled_channels[8 - channel] == '1'
        return start_enabled

    def enable_channel(self, channel, enable):
        start_enabled, enabled_channels = self.get_enabled_channels()

        if channel:
            enabled_channels = \
              replace_char(enabled_channels, 8 - channel, '1' if enable else '0')
        else:
            start_enabled = enable
        self.qutag.enableChannels(start_enabled, enabled_channels)

    def get_trigger_edge(self, channel):
        edge, threshold = self.qutag.getSignalConditioning(channel)
        return edge

    def set_trigger_edge(self, channel, edge):
        threshold = self.get_trigger_threshold(channel)
        self.qutag.setSignalConditioning(channel, self.SCOND_MISC, edge,
                                         threshold)

    def get_trigger_threshold(self, channel):
        edge, threshold = self.qutag.getSignalConditioning(channel)
        return threshold

    def set_trigger_threshold(self, channel, threshold):
        edge = self.get_trigger_edge(channel)
        self.qutag.setSignalConditioning(channel, self.SCOND_MISC, edge,
                                         threshold)

    def get_signal_conditioning(self, channel):
        return "Misc"

    def set_signal_conditioning(self, channel, cond):
        edge, threshold = self.qutag.getSignalConditioning(channel)
        self.qutag.setSignalConditioning(channel, cond, edge, threshold)

    def start_grabbing(self, callback, loop=None):
        if loop is None:
            loop = self.loop
        for i,get_count_rate in enumerate(self.get_count_rate):
            if get_count_rate:
                self.enable_channel(i+1, True)

        self._stop = False
        self.sample_count.fill(0)
        self.count_rate_channels = \
            [channel for channel,get_count_rate in enumerate(self.get_count_rate)
             if get_count_rate]

        self.callback = callback
        self.thread = Thread(target=loop)
        self.qutag.getLastTimestamps(reset=True)
        self.thread.start()
        return ['channel %d' % (c + 1) for c in self.count_rate_channels]

    def start_grabbing_hist(self, callback):
        return self.start_grabbing(callback, loop=self.hist_loop)

    def loop(self):
        previous_update = time.time()
        while not self._stop:
            result = self.qutag.getLastTimestamps(reset=True)
            if not range(result[2]):
                continue
            now = time.time()
            for i in range(result[2]): # loop over all events
                self.sample_count[result[1][i]] += 1

            dt = now - previous_update
            if dt < self.update_interval:
                continue

            data = [np.array([self.sample_count[channel] / dt])
                    for channel in self.count_rate_channels]

            previous_update = now
            self.sample_count.fill(0)
            if len(data):
                self.callback(data)

    def hist_loop(self):
        next_update = time.time() + self.update_interval
        time_tags = [[] for _ in range(len(self.count_rate_channels))]
        prev_channel = -1
        while not self._stop:
            result = self.qutag.getLastTimestamps(reset=True)
            if not range(result[2]):
                continue
            now = time.time()
            for i in range(result[2]): # loop over all events
                channel = result[1][i]
                if prev_channel == channel:
                    continue
                prev_channel = channel
                time_tags[channel].append(result[0][i] * 1e-6)

            if now < next_update:
                continue

            next_update = now + self.update_interval
            for i,t in enumerate(time_tags):
                time_tags[i] = np.array(t)
            self.callback(time_tags)
            time_tags = [[] for _ in range(len(self.count_rate_channels))]

    def diff_loop(self):
        next_update = time.time() + self.update_interval
        time_tags = [[] for _ in range(len(self.count_rate_channels))]
        start = False
        prev_channel = -1
        while not self._stop:
            result = self.qutag.getLastTimestamps(reset=True)
            if not range(result[2]):
                continue
            now = time.time()
            for i in range(result[2]): # loop over all events
                channel = result[1][i]
                if prev_channel == channel:
                    if not start:
                        start = True
                    continue
                prev_channel = channel
                if not start:
                    continue
                time_tags[channel].append(result[0][i] * 1e-6)

            if now < next_update:
                continue

            next_update = now + self.update_interval
            for i,t in enumerate(time_tags):
                time_tags[i] = np.array(t)
            self.callback(time_tags)
            time_tags = [[] for _ in range(len(self.count_rate_channels))]

    def stop(self):
        if self.thread is not None:
            self._stop = True
            self.thread.join()
            self.thread = None
        self.close_communication() # workaround for PyMoDAQ not calling that
