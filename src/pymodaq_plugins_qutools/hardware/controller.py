import ctypes, random, time
import numpy as np
from threading import Thread
from pymodaq_plugins_qutools.hardware.QuTAG_HR import QuTAG


class QuTAGController:

    def __init__(self):
        self.initialised = False
        self.thread = None

    def open_communication(self, update_interval):
        try:
            self.qutag = QuTAG(buf_size=1000)
        except:
            raise RuntimeError("Couldn't initialise QuTAG")
        self.update_interval = update_interval
        self.initialised = True

    def close_communication(self):
        if self.initialised:
            self.stop_tagging()
            self.qutag.deInitialize()
            self.initialised = False

    def is_enabled(self, channel):
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

    def start(self, channels, callback, update_interval):
        """Start measuring rates on channels."""

        if self.thread is not None:
            return
        self.callback = callback
        self.channels = channels
        self.update_interval = update_interval
        for channel in channels:
            self.enable_channel(channel, True)
        self._stop = False
        self.thread = Thread(target=self._loop)
        self.thread.start()
        
    def stop_events(self):
        """Finish event recording and stop thread loop."""
        if self.thread is None:
            return

        self._stop = True
        self.thread.join()
        self.callback = None
        self.thread = None

    def _loop(self):
        if not self.initialised:
            return
        self.events = []
        self.next_update = time.time() + self.update_interval
        while not self._stop:
            timestamps, channels, valid = self._get_time_stamps()
            now = time.time()
            self.events += list(zip(timestamps[:valid], channels[:valid]))

            if now > self.next_update:
                # send events on due time
                self.callback(self.events)
                self.events = []

    def _get_time_stamps(self):
        """Read time stamps from device."""

        timestamps, channels, valid = \
            self.qutag.getLastTimestamps(reset=True)
        now = time.time()
        time.sleep(0.01)
        return timestamps, channels, valid


class MockQuTAGController(QuTAGController):

    def open_communication(self, update_interval):
        self.update_interval = update_interval
        self.initialised = True
        self._enabled = [True for _ in range(9)]

    def close_communication(self):
        if self.initialised:
            self.stop_tagging()
            self.initialised = False

    def is_enabled(self, channel):
        return self._enabled[channel]

    def enable_channel(self, channel, enable):
        self._enabled[channel] = enable

    @classmethod
    def make_events(cls, t, to_time, rate):
        """Generate events according to Poisson distribution.
        Includes starting event at time==t."""

        events = []
        while t < to_time:
            events.append(t)
            t -= np.log(1.0 - random.random()) / rate
        return events, t

    def start(self, channels, callback, update_interval=None):
        """Fill self.last_timestamp[channel] with nows and start recording."""

        now = time.time()
        self.last_timestamp = [now for _ in range(len(channels) + 1)]
        super().start(channels, callback, update_interval)

    def _get_time_stamps(self):
        """Generate events since self.last_timestamp[channel]."""

        now = time.time()
        timestamps = []
        channels = []
        for channel in self.channels:
            events, self.last_timestamp[channel] = \
                self.make_events(self.last_timestamp[channel], now,
                                 self.rates[channel])
            timestamps += events
            channels += [channel for _ in range(len(events))]

        # bring lists into time order
        events = list(zip(timestamps, channels))
        events.sort()
        timestamps, channels = list(zip(*events))
        timestamps, channels = list(timestamps), list(channels)

        time.sleep(0.01) # don't go too fast
        return timestamps, channels, len(channels)
