import ctypes, random
import numpy as np
from threading import Thread
from pymodaq_plugins_qutools.hardware.QuTAG_HR import QuTAG

import time

def replace_char(string, pos, char):
    return string[:pos] + char + string[pos+1:]
# Could simply be string[pos] = char. However, in Python some features are
# just broken by design ;-/

class QuTAGController:

    SCOND_LVTTL = 1
    SCOND_NIM   = 2
    SCOND_MISC  = 3
     
    def __init__(self):
        self._initialised = False
        self.thread = None
        self.rates_callback = None
        self.rate_channels = None
        self._initialise_rates = False
        self.events_callback = None
        self.event_channels = None
        self._initialise_events = False
        self.sample_count = np.zeros(8, dtype=np.int32)
        self.time_tags_per_channel = True
        self.mean_valid = 0
        self.rms_valid = 0

    def __del__(self):
        self.close_communication()

    def open_communication(self, update_interval):
        try:
            self.qutag = QuTAG(buf_size=1000)
        except:
            raise RuntimeError("Couldn't initialise QuTAG")
        self.update_interval = update_interval
        self._initialised = True

    def close_communication(self):
        if self._initialised:
            self.stop_tagging()
            self.qutag.deInitialize()
            self._initialised = False

    @property
    def initialised(self):
        return self._initialised

    @property
    def collecting_events(self):
        return self.event_channels is not None

    @property
    def measuring_rates(self):
        return self.rate_channels is not None

    def set_update_interval(self, interval):
        self.update_interval = interval

    @property
    def enabled_channels(self):
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

    def start_events(self, channels, callback=None, update_interval=None,
                     time_tags_per_channel=True):
        self.events_callback = callback
        self.events_update_interval = update_interval
        self.time_tags_per_channel = time_tags_per_channel
        self.event_channels = channels
        for channel in channels:
            self.enable_channel(channel+1, True)
        self._initialise_events = True
        self._start_tagging()

    def start_rates(self, channels, callback=None, update_interval=None):
        self.rates_callback = callback
        self.rates_update_interval = update_interval
        self.rate_channels = channels
        for channel in channels:
            self.enable_channel(channel+1, True)
        self._initialise_rates = True
        self._start_tagging()

    def _start_tagging(self):
        if self.thread is not None:
            return
        self._stop = False
        self.thread = Thread(target=self._loop)
        self.thread.start()

    def _get_time_stamps(self):
        timestamps, channels, valid = \
            self.qutag.getLastTimestamps(reset=True)
        now = time.time()
        time.sleep(0.01)
        return timestamps, channels, valid

    def _get_time_tags(self):
        """Transforms list of tag lists into list of np.arrays."""
        time_tags = [np.array(t) for t in self._time_tags]
        self._time_tags = [[] for _ in range(len(self.event_channels))]
        return time_tags

    def _get_rates(self, now):
        """Transforms list of counts into list of np.arrays containing rates."""
        dt = now - self.rates_start
        self.rates_start = now
        data = [np.array([self.sample_count[channel-1] / dt])
                for channel in self.rate_channels]
        self.sample_count.fill(0)
        return data

    def stop_events(self):
        self.events_callback = None
        if self.rates_callback is None:
            self._stop_tagging()
        self.event_channels = None

    def stop_rates(self):
        self.rates_callback = None
        if self.events_callback is None:
            self._stop_tagging()

    def _stop_tagging(self):
        if self.thread is not None:
            self._stop = True
            self.thread.join()
            self.thread = None

# thread matter
    def _loop(self):
        self.qutag.getLastTimestamps(reset=True) # clear all
        while not self._stop:
            if not self._initialised:
                return

            timestamps, channels, valid = self._get_time_stamps()

            if self._initialise_events:
                self._clear_events(now)
                self._initialise_events = False

            if self._initialise_rates:
                self._clear_rates(now)
                self._initialise_rates = False

            for i in range(valid): # loop over all events and add them to the
                # corresponding tag list
                channel = channels[i]
                if self.time_tags_per_channel:
                    try:
                        self._time_tags[channel].append(timestamps[i] * 1e-6)
                    except:
                        pass # got nothing, ignore channel
                else:
                    self._time_tags.append([timestamps[i] * 1e-6, channel])
                try:
                    self.sample_count[channels[i]] += 1
                except:
                    pass # got nothing, ignore channel

            if self.rates_callback is not None and now > self.next_rates_update:
                rates = self._get_rates(now)
                if len(rates):
                    self.rates_callback(rates)
                self._clear_rates(now)

            if self.events_callback is not None \
               and now > self.next_events_update:
                time_tags = self._get_time_tags()
                self.events_callback(time_tags)
                self._clear_events(now)

    def _clear_events(self, now):
        if self.time_tags_per_channel:
            self._time_tags = [[] for _ in range(len(self.event_channels))]
        else:
            self._time_tags = []
        self.next_events_update = now + self.events_update_interval

    def _clear_rates(self, now):
        self.sample_count = np.zeros(len(self.rate_channels))
        self.next_rates_update = now + self.rates_update_interval
        self.rates_start = now


class MockQuTAGController(QuTAGController):

    
    def __init__(self):
        QuTAGController.__init__(self)
        self.rates = np.zeros(8)
        self.events = np.zeros(8)

    def open_communication(self, update_interval):
        self.update_interval = update_interval
        self._initialised = True

    def close_communication(self):
        self._initialised = False

    def _get_time_stamps(self):
        now = time.time()
        time.sleep(0.01)
        timestamps = []
        channels = []
        for channel in self.rate_channels:
            arrival = self.last_timestamp[channel]
            if arrival < now:
                while True:
                    p = random.random()
                    arrival += -numpy.log(1.0 - p) / self.rates[channel]
                    if arrival > now:
                        break
                    timestamps.append(arrival)
                    channels.append(channel)
                self.last_timestamp[channel] = arrival

        return timestamps, channels, len(channels)

    def start_rates(self, channels, callback=None, update_interval=None):
        now = time.time()
        self.last_timestamp = [now for _ in range(len(channels))]
        super().start_rates(channels, callback, update_interval)


class MockTAQuTAGController(QuTAGController):

    # rewrite and place into ps ta plugin
    def __init__(self):
        QuTAGController.__init__(self)

    def open_communication(self, update_interval):
        self.update_interval = update_interval
        self._initialised = True

    def close_communication(self):
        self._initialised = False

    def next_time_stamp(self, previous, rate):
        return previous - np.log(1.0 - random.random()) / rate        

    def _get_time_stamps(self):
        now = time.time()
        time.sleep(0.01)
        timestamps = []
        channels = []
        for channel in self.rate_channels:
            arrival = self.last_timestamp[channel]
            if arrival < now:
                while True:
                    arrival = \
                        next_time_stamp(self, arrival, self.rates[channel])
                    if arrival > now:
                        break
                    timestamps.append(arrival)
                    channels.append(channel)
                self.last_timestamp[channel] = arrival

        return timestamps, channels, len(channels)

    def start_rates(self, channels, callback=None, update_interval=None):
        now = time.time()
        self.last_timestamp = [now for _ in range(len(channels))]
        super().start_rates(channels, callback, update_interval)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    controller = MockTAQuTAGController()
    times = [0]
    n = 100000
    for _ in range(n):
        times.append(controller.next_time_stamp(times[-1], 100))

    dt = 10
    t_limit = dt
    current = 0
    rates = []
    for t in times:
        if t < t_limit:
            current += 1
        else:
            rates.append(current)
            t_limit += dt
            current = 0
    rates.append(current)

    n = len(rates)
    plt.plot(np.linspace(0, n-1, n) * dt, np.array(rates) / dt)
    plt.show()

    dt = 10
    t_end = 1000
    rate = 100

    n = int(t_end / dt)
    dt = t_end / n

    t = 0
    for i in range(n+1):
        t = controller.next_time_stamp(t, 100))
        
