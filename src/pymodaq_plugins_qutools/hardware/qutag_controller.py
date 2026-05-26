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
        """Return channels which are enabled on the device."""

        start_enabled, enabled_channels = self.qutag.getChannelsEnabled()
        while len(enabled_channels) < 8:
            enabled_channels = '0' + enabled_channels
        return start_enabled, enabled_channels

    def get_enabled(self, channel):
        """Return True if channel is enabled.
        0: start, 1:-8 normal channels."""

        start_enabled, enabled_channels = self.enabled_channels
        if channel:
            return enabled_channels[8 - channel] == '1'
        return start_enabled

    def enable_channel(self, channel, enable):
        """Enable or disable channel.
        0: start, 1:-8 normal channels."""

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
        """Start collecting events on channels."""

        self.events_callback = callback
        self.events_update_interval = update_interval
        self.time_tags_per_channel = time_tags_per_channel
        self.event_channels = channels
        for channel in channels:
            self.enable_channel(channel, True)
        self._initialise_events = True # flag for the first round in thread loop
        self._start_tagging()

    def start_rates(self, channels, callback=None, update_interval=None):
        """Start measuring rates on channels."""

        self.rates_callback = callback
        self.rates_update_interval = update_interval
        self.rate_channels = channels
        for channel in channels:
            self.enable_channel(channel, True)
        self._initialise_rates = True # flag for the first round in thread loop
        self._start_tagging()

    def _start_tagging(self):
        """Start thread loop if not already running."""

        if self.thread is not None:
            return
        self._stop = False
        self.thread = Thread(target=self._loop)
        self.thread.start()

    def _get_time_stamps(self):
        """Read time stamps from device."""

        timestamps, channels, valid = \
            self.qutag.getLastTimestamps(reset=True)
        now = time.time()
        time.sleep(0.01)
        return timestamps, channels, valid

    def _get_time_tags(self):
        """Transform list of tag lists into list of np.arrays."""

        time_tags = [np.array(t) for t in self._time_tags]
        self._time_tags = [[] for _ in range(len(self.event_channels))]
        return time_tags

    def _get_rates(self, now):
        """Transform list of counts into list of np.arrays containing rates."""

        dt = now - self.rates_start
        self.rates_start = now
        data = [np.array([self.sample_count[channel-1] / dt])
                for channel in self.rate_channels]
        self.sample_count.fill(0)
        return data

    def stop_events(self):
        """Finish event recording, stop thread loop if not measuring rates."""

        self.events_callback = None
        if self.rates_callback is None:
            self._stop_tagging()
        self.event_channels = None

    def stop_rates(self):
        """Finish measurng rates, stop thread loop if not collecting events."""

        self.rates_callback = None
        if self.events_callback is None:
            self._stop_tagging()

    def _stop_tagging(self):
        """Stop thread loop and wait until thread has finished."""

        if self.thread is not None:
            self._stop = True
            self.thread.join()
            self.thread = None

# thread matter
    def _loop(self):
        self._get_time_stamps() # clear all
        while not self._stop:
            if not self._initialised:
                return

            timestamps, channels, valid = self._get_time_stamps()

            # initialise at first round if asked for
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
                # send rates on due time
                rates = self._get_rates(now)
                if len(rates):
                    self.rates_callback(rates)
                self._clear_rates(now)

            if self.events_callback is not None \
               and now > self.next_events_update:
                # send events on due time
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

    # rewrite and place into ps ta plugin
    def __init__(self):
        QuTAGController.__init__(self)
        self._enabled = [True for _ in range(9)]

    def open_communication(self, update_interval):
        self.update_interval = update_interval
        self._initialised = True

    def close_communication(self):
        self._initialised = False

    @classmethod
    def make_events(cls, t, to_time, rate):
        """Generate events according to Poisson distribution.
        Includes starting event at time==t."""

        events = []
        while t < to_time:
            events.append(t)
            t -= np.log(1.0 - random.random()) / rate
        return events, t

    def _get_time_stamps(self):
        """Generate events since self.last_timestamp[channel]."""

        now = time.time()
        timestamps = []
        channels = []
        for channel in self.rate_channels:
            events, self.last_timestamp[channel] = \
                self.make_events(self.last_timestamp[channel], now,
                                 self.rates[channel])
            timestamps += events
            channels += [channel for _ in range(len(events))]

        # bring lists into time order
        events = list(zip(timestams, channels))
        events.sort()
        timestamps, channels = list(zip(*events))

        time.sleep(0.01) # don't go too fast
        return timestamps, channels, len(channels)

    def start_rates(self, channels, callback=None, update_interval=None):
        """Fill self.last_timestamp[channel] with nows and start recording."""

        now = time.time()
        self.last_timestamp = [now for _ in range(len(channels))]
        super().start_rates(channels, callback, update_interval)

    @property
    def enabled_channels(self):
        return self._enabled[0], ['1' if c else '0' for c in self._enabled]

    def get_enabled(self, channel):
        return self._enabled[channel]

    def enable_channel(self, channel, enable):
        try:
            self._enabled[channel] = enable
        except:
            breakpoint()


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    dt = 10
    t_end = 1000
    rate = 100

    n = int(t_end / dt)
    dt = t_end / n
    rates = []

    t = 0
    for i in range(n+1):
        end_bin = (i + 1) * dt
        events, t = MockTAQuTAGController.make_events(t, end_bin, rate)
        rates.append(len(events))

    plt.plot(range(n+1), rates)
    plt.show()
