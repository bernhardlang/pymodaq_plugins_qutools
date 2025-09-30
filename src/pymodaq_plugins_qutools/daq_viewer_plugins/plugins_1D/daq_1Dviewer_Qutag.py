import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.qutag_controller import QuTAGController


class DAQ_1DViewer_Qutag(DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG 1D viewer.
    """

    conditioning = [
        { 'title': 'Signal Conditioning', 'name': 'signal_cond', 'type': 'list',
          'limits': ['LVTTL', 'NIM', 'Misc'] },
        { 'title': 'Trigger Edge', 'name': 'trigger_edge', 'type': 'list',
          'limits': ['Rising', 'Falling'] },
        { 'title': 'Trigger Threshold', 'name': 'trigger_threshold',
          'type': 'float', 'min': -2, 'max': 3 },
    ]

    channel_settings = conditioning + [
        { 'title': 'Enabled?', 'name': 'enabled', 'type': 'bool',
          'value': True },
        { 'title': 'Get Count Rate?', 'name': 'get_count_rate', 'type': 'bool',
          'value': False },
    ]

    start_settings = conditioning + [
        { 'title': 'Enabled?', 'name': 'enabled', 'type': 'bool',
          'value': True },
    ]

    params = comon_parameters+[
        { 'title': 'Update Interval [s]', 'name': 'update_interval',
          'type': 'float', 'value': 1 },
        { 'title': 'Grab all enabled channels?', 'name': 'grab_enabled',
          'type': 'bool', 'value': True },
        { 'title': 'Histogram bins', 'name': 'n_bins',
          'type': 'bool', 'value': True },
        { 'title': 'Calculate difference', 'name': 'calculate_difference',
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

    def ini_attributes(self):
        self.controller: QuTAGController = None
        self.n_bins = 20
        self.live = False

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
            if self.settings.child("grab_enabled").value() \
               or self.settings.child("line_settings") \
                               .child("settings_ch%d" % channel) \
                               .child("get_count_rate").value():
                channels.append(channel)
        return channels
        
    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible,
            self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                channels = self.determine_active_channels()
                update_interval = self.settings.child("update_interval").value()
                self.channel_list = \
                    self.controller.start_events(channels, self.callback,
                                                 update_interval)
            elif self.live:
                self.live = False
                self.controller.stop_events()
            return

        if not self.controller.collecting_events:
            channels = self.determine_active_channels()
            self.channel_list = self.controller.start_events(channels)
            return

        time_tags = self.controller.grab_time_tags()
        self.callback(time_tags)

    def callback(self, time_tags):
        data = []
        if self.settings.child('calculate_difference').value():
            n_tags = min(len(time_tags[0]), len(time_tags[1]))
            diff = np.empty(n_tags)
            for i in range(n_tags):
                diff[i] = time_tags[1][i] - time_tags[0][i]
            time_tags.append(diff)

        for channel,tags in enumerate(time_tags):
            if not len(tags):
                continue
            min_val = min(tags)
            max_val = max(tags)
            bin_size = (max_val - min_val) / self.n_bins
            centers = np.linspace(min_val + 0.5 * bin_size,
                                  max_val - 0.5 * bin_size, self.n_bins)
            bins = np.zeros(self.n_bins)
            for tag in tags:
                idx = int((tag - min_val) / bin_size)
                if idx >= 0 and idx < self.n_bins:
                    bins[idx] += 1
            try:
                label = self.active_channel_list[channel]
            except:
                label = 'difference'

            dfp = DataFromPlugins(name='qutag', data=bins, dim='Data1D',
                                  labels=[label],
                                  axes=[Axis(data=centers, label='', units='',
                                             index=0)])
            data.append(dfp)

        self.dte_signal.emit(DataToExport(name='qutag', data=data))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop_events()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG hist halted']))
        return ''


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__, init_h5=False)
