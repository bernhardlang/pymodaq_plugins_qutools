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
        self.rates_callback = None
        self.initialise_rates = False
        self.event_callback = None
        self.initialise_events = False
        self.sample_count = np.zeros(8, dtype=np.int32)
        self.alternate_only = True 

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
            self.stop_tagging()
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

    def start_events(self, channels, callback=None, update_interval=None):
        self.events_callback = callback
        self.events_update_interval = update_interval
        self.event_channels, channel_names = self.get_channel_list(channels)
        self.initialise_events = True
        self.start_tagging()
        return channel_names

    def start_rate(self, channels, callback=None, update_interval=None):
        self.rates_callback = callback
        self.rates_update_interval = update_interval
        self.rate_channels, channel_names = self.get_channel_list(channels)
        self.initialise_rates = True
        self.start_tagging()
        self.start_rates = True
        return channel_names

    def get_channel_list(self, channels):
        channel_list = []
        channel_names = []
        for channel in channels:
            self.enable_channel(channel+1, True)
            channel_list.append(channel)
            channel_names.append('channel %d' % (channel + 1))
        return channel_list, channel_names

    def start_tagging(self):
        if self.thread is not None:
            return
        self._stop = False
        self.thread = Thread(target=self.loop)
        self.qutag.getLastTimestamps(reset=True)
        self.thread.start()

    def grab_time_tags(self):
        time_tags = [np.array(t) for t in self.time_tags]
        self.time_tags = [[] for _ in range(len(self.event_channels))]
        return time_tags

    def grab_rates(self, now):
        dt = now - self.rates_start
        self.rates_start = now
        data = [np.array([self.sample_count[channel] / dt])
                for channel in self.rate_channels]
        self.sample_count.fill(0)
        return data
        
    def stop_events(self):
        self.event_callback = None
        if self.rates_callback is None:
            self.stop_tagging()

    def stop_rate(self):
        self.rates_callback = None
        if self.event_callback is None:
            self.stop_tagging()

    def stop_tagging(self):
        if self.thread is not None:
            self._stop = True
            self.thread.join()
            self.thread = None

# thread matter
    def loop(self):
        prev_channel = -1
        while not self._stop:
            if not self.initialised:
                return

            result = self.qutag.getLastTimestamps(reset=True)
            now = time.time()

            if self.initialise_events:
                self.clear_events(now)
                self.initialise_events = False

            if self.initialise_rates:
                self.clear_rates(now)
                self.initialise_rates = False

            for i in range(result[2]): # loop over all events
                channel = result[1][i]
                if self.alternate_only and prev_channel == channel:
                    continue
                prev_channel = channel
                try:
                    self.time_tags[channel].append(result[0][i] * 1e-6)
                except:
                    pass
                try:
                    self.sample_count[result[1][i]] += 1
                except:
                    pass

            if not self.initialise_rates and self.rates_callback is not None \
               and now > self.next_rates_update:
                rates = self.grab_rates(now)
                if len(rates):
                    self.rates_callback(rates)
                self.clear_rates(now)

            if not self.initialise_events and self.events_callback is not None \
               and now > self.next_events_update:
                time_tags = self.grab_time_tags()
                self.events_callback(time_tags)
                self.clear_events(now)

    def clear_events(self, now):
        self.time_tags = [[] for _ in range(len(self.event_channels))]
        self.next_events_update = now + self.events_update_interval

    def clear_rates(self, now):
        self.sample_count = np.zeros(len(channels))
        self.next_rates_update = now + self.rates_update_interval
        self.rates_start = now
