from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters
from pymodaq_gui.parameter import Parameter
from pymodaq_utils.utils import ThreadCommand
from pymodaq_plugins_qutools.hardware.controller import QuTAGController, \
    MockQuTAGController, channel_settings


class QutagCommon(DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG OD viewer.
    """

    params = comon_parameters + [
        { 'title': 'Update Interval [s]', 'name': 'update_interval',
          'type': 'float', 'value': 1 },
       ] + channel_settings

    live_mode_available = True
    simulate = False

    @property
    def _channel(self):
        return self.settings['channel']

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been
            changed by the user
        """
        if param.name() == "signal_cond":
            self.controller.set_signal_conditioning(self._channel, param.value())
        elif param.name() == "trigger_edge":
            self.controller.set_trigger_edge(self._channel, param.value())
        elif param.name() == "trigger_threshold":
            self.controller.set_trigger_threshold(self._channel, param.value())
        elif param.name() == "update_interval":
            self.controller.update_intervals[self._channel] = param.value()
        if param_name() == 'channel':
            self._channel_changed()

    def _channel_changed(self):
        self.controller.set_signal_conditioning(self._channel,
                                                self.settings['signal_cond'])
        self.controller.set_trigger_edge(self._channel,
                                         self.settings['trigger_edge'])
        self.controller.set_trigger_threshold(self._channel,
                                              self.settings['trigger_threshold'])
        self.controller.update_intervals[self._channel] = \
            self.settings['update_interval']

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
            self.controller = MockQuTAGController() if self.simulate else \
                QuTAGController()
            self.controller.open_communication()
            initialized = self.controller.initialised
        else:
            self.controller = controller
            initialized = True

        info = "Connected to quTAG"
        return info, initialized

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
            channel = self._channel
            if kwargs['live']:
                self._set_params()
                self.live = True
                if channel:
                    self.controller.start(self._channel, self.callback,
                                          self._external_trigger,
                                          self.settings['update_interval'])
                else:
                    self.controller.start_rate_zero(self.callback,
                                          self.settings['update_interval'])
            elif self.live:
                self.live = False
                self.controller.stop(self._channel)

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop(self._channel)
        self.emit_status(ThreadCommand('Update_Status', ['quTAG rate halted']))
        return ''

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.close_communication()

    def _set_params(self):
        pass

    @property
    def _external_trigger(self):
        return False
