from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters
from pymodaq_utils.utils import ThreadCommand
from pymodaq_plugins_qutools.hardware.controller import QuTAGController, \
    MockQuTAGController, channel_settings


class QutagCommon(DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG OD viewer.
    """

    params = comon_parameters + [
        { 'title': 'Channel', 'name': 'channel', 'type': 'int', 'min': 1,
          'max': 8, 'value': 1 },
        { 'title': 'Update Interval [s]', 'name': 'update_interval',
          'type': 'float', 'value': 1 },
       ] + channel_settings

    live_mode_available = True
    simulate = False

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
            if kwargs['live']:
                self.live = True
                self.controller.start(self.settings['channel'], self.callback,
                                      False, self.settings['update_interval'])
            elif self.live:
                self.live = False
                self.controller.stop(self.settings['channel'])

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop(self.settings['channel'])
        self.emit_status(ThreadCommand('Update_Status', ['quTAG rate halted']))
        return ''
