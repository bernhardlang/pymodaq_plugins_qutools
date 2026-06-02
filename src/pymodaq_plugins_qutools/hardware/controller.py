import ctypes, random, time
import numpy as np
from threading import Thread, Lock
from pymodaq_plugins_qutools.hardware.QuTAG_HR import QuTAG


channel_settings = [
    { 'title': 'Signal Conditioning', 'name': 'signal_cond', 'type': 'list',
      'limits': ['LVTTL', 'NIM', 'Misc'] },
    { 'title': 'Trigger Edge', 'name': 'trigger_edge', 'type': 'list',
      'limits': ['Rising', 'Falling'] },
    { 'title': 'Trigger Threshold', 'name': 'trigger_threshold',
      'type': 'float', 'min': -2, 'max': 3 },
]


class QuTAGController:

    def __init__(self):
        self.initialised = False
        self.thread = None
        self.update_intervals = [None for _ in range(9)]
        self.last_updates = [None for _ in range(9)]
        self.next_updates = [None for _ in range(9)]
        self.callbacks = [None for _ in range(9)]
        self.timestamps = [[] for _ in range(9)]
        self.last_channel_zero = 0
        self.active_channels = 0
        self.channel_zero_as_start = [False for _ in range(9)]
        self.mutex = Lock()

    def open_communication(self):
        try:
            self.qutag = QuTAG(buf_size=1000)
            self.initialised = True
        except:
            raise RuntimeError("Couldn't initialise QuTAG")

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

    def start_rate_zero(self, callback, update_interval):
        self._start(0, callback, False, update_interval)

    def start(self, channel, callback, channel_zero_as_start, update_interval):
        """Start measuring rates on channels."""

        assert channel > 0 and channel < 9
        self._start(channel, callback, channel_zero_as_start, update_interval)

    def _start(self, channel, callback, channel_zero_as_start, update_interval):
        if not self.initialised:
            return
        assert self.callbacks[channel] is None

        self.update_intervals[channel] = update_interval
        self.timestamps[channel] = []
        now = time.time()
        self.last_updates[channel] = now
        self.next_updates[channel] = now + update_interval

        self.callbacks[channel] = callback
        self.enable_channel(channel, True)
        if channel:
            self.channel_zero_as_start[channel] = channel_zero_as_start
            if channel_zero_as_start:
                self.enable_channel(0, True)
        self._start_loop()
        
    def stop(self, channel):
        """Finish event recording and stop thread loop."""

        if self.callbacks[channel] is None:
            return

        if channel:
            self.enable_channel(channel, False)
        self.callbacks[channel] = None
        self.next_updates[channel] = None
        self._stop_loop()

    def _start_loop(self):
        with self.mutex:
            self.active_channels += 1
            if self.thread is None:
                self.thread = Thread(target=self._loop)
                self._stop = False
                self.thread.start()

    def _stop_loop(self):
        with self.mutex:
            self.active_channels -= 1
            if not self.active_channels:
                self._stop = True
                self.thread.join()
                self.thread = None

    def _loop(self):
        while not self._stop:
            timestamps, channels, valid = self._get_time_stamps()
            now = time.time()
            for timestamp,channel in zip(timestamps[:valid], channels[:valid]):
                if channel and self.channel_zero_as_start[channel]:
                    timestamp -= self.last_channel_zero
                if self.callbacks[channel]:
                    self.timestamps[channel].append(timestamp)
                if not channel:
                    self.last_channel_zero = timestamp

            for channel,next_update in enumerate(self.next_updates):
                if next_update is None or now < next_update \
                   or self.callbacks[channel] is None:
                    continue
                self.callbacks[channel](self.timestamps[channel],
                                        now - self.last_updates[channel])
                self.timestamps[channel] = []
                self.last_updates[channel] = now
                self.next_updates[channel] = \
                    now + self.update_intervals[channel]

    def _get_time_stamps(self):
        """Read time stamps from device.
        Returns tuple (timestamps, channels, valid)."""

        return self.qutag.getLastTimestamps(reset=True)


class TAQuTAGController:

    def __init__(self):
        self.initialised = False
        self.thread = None
        self.update_interval = 1
        self.excitation_channel = 1
        self.probe_channel = 2
        self.callback = None
        self.mutex = Lock()

    def open_communication(self):
        try:
            self.qutag = QuTAG(buf_size=1000)
            self.initialised = True
        except:
            raise RuntimeError("Couldn't initialise QuTAG")

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

    def start(self, excitation_channel, probe_channel, callback):
        with self.mutex:
            if self.thread is not None:
                return
            self.excitation_channel = excitation_channel
            self.probe_channel = probe_channel
            self.callback = callback
            self.thread = Thread(target=self._loop)
            self._stop = False
            self.thread.start()

    def _loop(self):
        items = []
        while not self._stop:
            timestamps, channels, valid = self._get_time_stamps()
            now = time.time()
            probe_laser = None
            excitation_laser = None
            for timestamp,channel in zip(timestamps[:valid], channels[:valid]):
                if not channel:
                    excitation_trigger = timestamp
                elif excitation_trigger is None:
                    continue

                elif channel == self.excitation_channel:
                    excitation_laser = timestamp - excitation_trigger
                elif channel == self.probe_channel:
                    if probe_laser is None:
                        probe_laser = timestamp - excitation_trigger
                else:
                    continue

                if excitation_laser is None or probe_laser is None:
                    continue

                items.append([excitation_laser, probe_laser])
                probe_laser = None
                excitation_laser = None

            if now < next_update:
                self.callback(items)
                items = []
                self.next_update = now + self.update_interval

    def _get_time_stamps(self):
        """Read time stamps from device.
        Returns tuple (timestamps, channels, valid)."""

        return self.qutag.getLastTimestamps(reset=True)
        

class MockQuTAGController(QuTAGController):

    def open_communication(self):
        self.initialised = True
        self._enabled = [True for _ in range(9)]
        self.rates = [1e4 for _ in range(9)]
        self.rates[0] = 1e3
        self.lifetimes = [0 for _ in range(9)]
        self.backgrounds = [0 for _ in range(9)]
        self.last_timestamp = [None for _ in range(9)]
        self.external_trigger = False
        self.zero_as_start = False

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

    @classmethod
    def make_exp_events(cls, triggers, rate, lifetime):
        events = []
        events_per_trigger = rate * (triggers[-1] - triggers[0]) / len(triggers)
        events = \
            [t + np.random.exponential(lifetime)
             for i in range(np.random.poisson(events_per_trigger))
             for t in triggers]
        events.sort()
        return events

    def start(self, channel, callback, channel_zero_as_start, update_interval):
        """Fill self.last_timestamp[channel] with nows and start recording."""

        assert channel > 0 and channel < 9
        self.last_timestamp[channel] = time.time()
        self.zero_as_start |= channel_zero_as_start
        if channel_zero_as_start and self.last_timestamp[0] is None:
            self.last_timestamp[0] = time.time()
            self.external_trigger = True
        super().start(channel, callback, channel_zero_as_start, update_interval)

    def start_rate_zero(self, callback, update_interval):
        self.last_timestamp[0] = time.time()
        super().start_rate_zero(callback, update_interval)

    def _get_time_stamps(self):
        """Generate events since self.last_timestamp[channel]."""

        now = time.time()
        if self.external_trigger or self.callbacks[0]:
            if self.external_trigger:
                dt = 1 / self.rates[0]
                n = int((now - self.last_timestamp[0]) / dt + 1)
                timestamps = [self.last_timestamp[0] + i * dt for i in range(n)]
            else:
                events, self.last_timestamp[0] = \
                    self.make_events(self.last_timestamp[0], now, self.rates[0])
                timestamps = events
            self.last_timestamp[0] = timestamps[-1]
            n_triggers = len(timestamps)
            channels = [0 for _ in range(n_triggers)]
        else:
            timestamps = []
            channels = []
            n_triggers = 0

        for channel in range(1, 9):
            if self.callbacks[channel] is None:
                continue
            if self.lifetimes[channel]:
                events = \
                    self.make_exp_events(timestamps[:n_triggers],
                                         self.rates[channel],
                                         self.lifetimes[channel])
                background_events, dummy = \
                    self.make_events(timestamps[0], now,
                                     self.backgrounds[channel])
            else:
                lt = self.last_timestamp[channel]
                events, self.last_timestamp[channel] = \
                    self.make_events(self.last_timestamp[channel], now,
                                     self.rates[channel])
                background_events, dummy = \
                    self.make_events(lt, now, self.backgrounds[channel])
            events += background_events
            timestamps += events
            channels += [channel for _ in range(len(events))]

        # bring lists into time order
        if len(timestamps):
            events = list(zip(timestamps, channels))
            events.sort()
            timestamps, channels = list(zip(*events))
            timestamps, channels = list(timestamps), list(channels)

        time.sleep(0.01) # don't go too fast
        return timestamps, channels, len(channels)


class MockTAQuTAGController(QuTAGController):

    def open_communication(self):
        self.initialised = True

    def close_communication(self):
        if self.initialised:
            self.stop_tagging()
            self.initialised = False

    @classmethod
    def _get_pulse(cls, when, jitter):
        return np.random.normal(when, jitter)

    def _get_time_stamps(self):
        now = time.time()
        dt = 1 / self.trigger_rate
        n = int((now - self.last_timestamp) / dt + 1)
        start = self.last_timestamp
        excitation = \
            [self._get_pulse(start + i * dt + self.excitation_laser,
                             self.excitation_jitter)
             for i in n]
        probe1 = \
            [self._get_pulse(start + i * dt + self.probe_laser, 50e-12)
             for i in n]
        probe2 = \
            [self._get_pulse(start + i * dt + self.probe_laser + dt / 2, 50e-12)
             for i in n]
        timestamps = excitation + probe1 + probe2
        channels = \
            [self.excitation_channel for _ in range(len(excitation))] \
            + [self.probe_channel for _ in range(2 * len(probe1))]

        if len(timestamps):
            events = list(zip(timestamps, channels))
            events.sort()
            timestamps, channels = list(zip(*events))
            timestamps, channels = list(timestamps), list(channels)

        return timestamps, channels, len(channels)
