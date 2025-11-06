import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.qutag_controller import QuTAGController


class QutagCommon:
    conditioning = [
        { 'title': 'Signal Conditioning', 'name': 'signal_cond', 'type': 'list',
          'limits': ['LVTTL', 'NIM', 'Misc'] },
        { 'title': 'Trigger Edge', 'name': 'trigger_edge', 'type': 'list',
          'limits': ['Rising', 'Falling'] },
        { 'title': 'Trigger Threshold', 'name': 'trigger_threshold',
          'type': 'float', 'min': -2, 'max': 3 },
    ]

    channel_settings = conditioning + [
        { 'title': 'Enabled', 'name': 'enabled', 'type': 'bool',
          'value': True },
        { 'title': 'Get Count Rate?', 'name': 'get_count_rate', 'type': 'bool',
          'value': False },
    ]

    start_settings = conditioning + [
        { 'title': 'Enabled', 'name': 'enabled', 'type': 'bool',
          'value': True },
    ]

    common_parameters = [
        { 'title': 'Update Interval [s]', 'name': 'update_interval',
          'type': 'float', 'value': 1 },
        { 'title': 'Grab all enabled channels', 'name': 'grab_enabled',
          'type': 'bool', 'value': True },
        { 'title': 'Line Settings', 'name': 'line_settings', 'type': 'group',
          'expanded': False, 'children': [
              { 'title': 'Start', 'name': 'settings_start', 'type': 'group',
                'expanded': False, 'children': start_settings},
              { 'title': 'Ch1', 'name': 'settings_ch1', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              { 'title': 'Ch2', 'name': 'settings_ch2', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              { 'title': 'Ch3', 'name': 'settings_ch3', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              { 'title': 'Ch4', 'name': 'settings_ch4', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              { 'title': 'Ch5', 'name': 'settings_ch5', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              { 'title': 'Ch6', 'name': 'settings_ch6', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              { 'title': 'Ch7', 'name': 'settings_ch7', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              { 'title': 'Ch8', 'name': 'settings_ch8', 'type': 'group',
                'expanded': False, 'children': channel_settings},
              ]
          }]

    live_mode_available = True

    def get_channel_from_param_name(self, parent_name):
        if parent_name == "settings_start":
            return 0
        try:
           assert parent_name[:11] == "settings_ch"
           channel = int(parent_name[11:])
           assert channel >= 1 and channel <= 8
        except:
            return -1
        return channel

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been
            changed by the user
        """
        if param.name() == "update_interval":
            self.controller.set_update_interval(param.value())
            return
        if param.name() == "num_bins":
            self.n_bins = param.value()
            return
        if param.name() == "calculate_difference":
            self.calculate_difference = param.value()
            return

        channel = self.get_channel_from_param_name(param.parent().name())
        if channel < 0:
            return

        if param.name() == "enabled":
            self.controller.enable_channel(channel, param.value())
        elif param.name() == "get_count_rate":
            self.controller.get_count_rate[channel] = 1 if param.value() else 0
        elif param.name() == "signal_cond":
            self.controller.set_signal_conditioning(channel, param.value())
        elif param.name() == "trigger_edge":
            self.controller.set_trigger_edge(channel, param.value())
        elif param.name() == "trigger_threshold":
            self.controller.set_trigger_threshold(channel, param.value())

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one
            actuator/detector by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:
            self.controller = QuTAGController()
            update_interval = self.settings.child('update_interval').value()
            self.controller.open_communication(update_interval)
            initialized = self.controller.is_initialised()
        else:
            self.controller = controller
            initialized = True

        self.controller.qutag.enableChannels(True)
        for channel in range(9):
            if channel:
                settings_name = 'settings_ch%d' % channel
            else:
                settings_name = 'settings_start'
            val = self.controller.get_signal_conditioning(channel)
            self.settings.child('line_settings').child(settings_name)\
                                            .child('signal_cond').setValue(val)
            val = self.controller.get_trigger_edge(channel)
            self.settings.child('line_settings').child(settings_name)\
                                                .child('trigger_edge')\
                .setValue(val)
            val = self.controller.get_trigger_threshold(channel)
            self.settings.child('line_settings').child(settings_name)\
                                                .child('trigger_threshold')\
                .setValue(val)
            val = self.controller.get_enabled(channel)
            self.settings.child('line_settings').child(settings_name)\
                                                .child('enabled').setValue(val)

        info = "Connected to quTAG"
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.close_communication()

    def activate_grabbing(self, channel, enable):
        channel_key = ('settings_ch%d' % channel) if channel \
            else 'settings_start'
        self.settings.child("line_settings").child(channel_key)\
            .child('get_count_rate').setValue(enable)

    def determine_active_channels(self):
        channels = []
        for channel in range(1,9):
            if not self.controller.get_enabled(channel):
                continue
            # <<-- revise this
            if self.settings.child("grab_enabled").value() \
               or self.settings.child("line_settings") \
                               .child("settings_ch%d" % channel) \
                               .child("get_count_rate").value():
                channels.append(channel)
        return channels


class Histogram:

    def __init__(self, n_bins, min_val=None, max_val=None):
        self.n_bins = n_bins
        if isinstance(min_val, list) or isinstance(min_val, np.ndarray):
            self.values = min_val
            self._set_up()
        elif min_val is not None:
            self.set_up(min_val, max_val)
            self._changed = False
            self.values = None
        else:
            self.values = []
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

    def _set_up(self):
        if not len(self.values):
            self.set_up(0, 1)
            return
        self.set_up(min(self.values), max(self.values))
        for value in self.values:
            self.add(value)

    def add(self, value):
        idx = int((value - self.start_range) / self.bin_width)
        if idx >= 0:
            try:
                self._bins[idx] += 1
            except:
                pass

    def collect(self, value):
        self.values.append(value)

    @property
    def bins(self):
        if not hasattr(self, '_bins'):
            self._set_up()
            self._update()
        return self._bins

    @property
    def centers(self):
        if not hasattr(self, '_centers'):
            self._set_up()
            self._update()
        return self._centers

    @property
    def samples(self):
        if self._changed:
            self._update()
        return self._samples

    @property
    def mean(self):
        if self._changed:
            self._update()
        return self._mean
    
    @property
    def sigma(self):
        if self._changed:
            self._update()
        return self._sigma

    @property
    def normalised_bins(self):
        if self._changed:
            self._update()
        return self._normalised_bins

    def _update(self):
        if not hasattr(self, '_bins'):
            self._set_up()
            if not len(self.values):
                self._samples = 0
                self._normalised_bins = self._bins
                self._mean = 0
                self._sigma = 0
                self._changed = False
                return
            self.values = []

        self._samples = sum(self._bins)
        self._normalised_bins = self._bins / (self._samples * self.bin_width)
        self._mean = \
            np.dot(self._normalised_bins, self._centers) * self.bin_width
        self._sigma = \
            np.sqrt(np.dot(self._normalised_bins,
                           (self._centers - self._mean)**2)
                    * self.bin_width)

        self._changed = False
