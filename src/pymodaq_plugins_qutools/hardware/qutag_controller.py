import numpy as np
from threading import Thread
from pymodaq_plugins_qutools.hardware.QuTAG_HR import QuTAG

import time


class QuTAGController:

    SCOND_LVTTL = 1
    SCOND_NIM   = 2
    SCOND_MISC  = 3
     
    def __init__(self):
        self.initialised     = False
        self.thread          = None
        self.channel_active  = np.zeros(9, dtype=np.int32) # 0-8
#        self.samples         = [None for _ in range(8)]
#        self.max_samples     = np.full(8, 500, dtype=np.int32)
#        self.n_samples       = np.zeros(8, dtype=np.int32)
#        self.n_bins          = np.full(8, 20, dtype=np.int32)
#        self.callback        = [None for _ in range(8)]
        self.active_channels = 0

    def __del__(self):
        if self.thread is not None:
            self.stop()
        if self.initialised:
            self.qutag.deInitialize()

    def open_communication(self):
        try:
            self.qutag = QuTAG()
        except:
            raise RuntimeError("Couldn't initialise QuTAG")
        self.initialised = True

    def close_communication(self):
        if self.initialised:
            self.qutag.deInitialize()
            self.initialised = False

    def is_initialised(self):
        return self.initialised

    def get_enabled(self, channel):
        start_enabled, channels_enabled = self.qutag.getChannelsEnabled()
        while len(channels_enabled) < 8:
            channels_enabled = '0' + channels_enabled
        if channel:
            return channels_enabled[8 - channel] == '1'
        return start_enabled

    def enable_channel(self, channel, enable):
        start_enabled, channels_enabled = self.qutag.getChannelsEnabled()
        while len(channels_enabled) < 8:
            channels_enabled = '0' + channels_enabled

        if channel:
#            channels_enabled[channel-1] = '1' if enable else '0'
# In Python some features are just broken by design  :-/
            if enable:
                channels_enabled[:channel-1] + '1' + channels_enabled[:channel]
            else:
                channels_enabled[:channel-1] + '0' + channels_enabled[:channel]
        else:
            start_enabled = enable
        self.qutag.enableChannels(start_enabled, channels_enabled)

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

    def start_grabbing(self):
        self.thread = Thread(target=self.loop)
        self._stop = False
        for i,active in enumerate(self.channel_active):
            if active:
                self.enable_channel(i, True)
        self.qutag.getLastTimestamps(reset=True)
        self.starting_time = np.full(8, time.time())
        self.rates = np.zeros(8)
        self.sample_count = np.zeros(8, dtype=np.int32)
        self.update_start = [True for _ in range(9)]
        self.thread.start()

    def loop(self):
        while not self._stop:
            result = self.qutag.getLastTimestamps(reset=True)
            now = time.time()
            for i in range(result[2]): # loop over all events
                channel = result[1][i]
                if self.channel_active[channel]:
                    self.sample_count[channel] += 1
            for channel,active in enumerate(self.channel_active):
                if not active:
                    continue
                if self.update_start[channel]: # rate has recently been grabbed
                    self.update_start[channel] = False
                    self.starting_time[channel] = now
                else:
                    self.rates[channel] = \
                        self.sample_count[channel] \
                        / (now - self.starting_time[channel])

    def get_rate(self, channel):
        result = self.rates[channel]
        if not self.update_start[channel]: # handshaking with thread loop
            self.update_start[channel] = True
        return result

    def get_rates(self):
        rates = []
        for i,active in enumerate(self.channel_active):
            if not active:
                continue
            rates.append(np.array([self.rates[i]]))
            if not self.update_start[i]: # handshaking with thread loop
                self.update_start[i] = True
        return rates

    def start_histogram(self, channel, callback):
        self.send_histogram[channel] = True
        self.start(channel, callback)

    def make_histogram(self, channel):
        n_bins = self.n_bins[channel]
        from_range = min(self.samples[channel][:self.n_samples[channel]])
        to_range = max(self.samples[channel][:self.n_samples[channel]])
        bin_width = (to_range - from_range) / n_bins
        centers = np.linspace(from_range + bin_width / 2,
                              to_range - bin_width / 2, n_bins)
        bins = np.zeros(n_bins)
        for val in self.samples[channel][:self.max_samples[channel]]:
            idx = int((val - from_range) / bin_width)
            if idx >= 0 and idx < n_bins:
                bins[idx] += 1
        centers = np.linspace(from_range + bin_width / 2,
                              to_range - bin_width / 2, n_bins)
        return centers, bins

    def stop(self):
        if self.thread is not None:
            self._stop = True
            self.thread.join()
            self.thread = None
        self.close_communication() # workaround for PyMoDAQ not calling that
