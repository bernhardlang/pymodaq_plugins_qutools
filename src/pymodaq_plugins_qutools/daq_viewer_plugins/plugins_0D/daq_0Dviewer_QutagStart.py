import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.controller import QuTAGController, \
    channel_settings


class DAQ_0DViewer_QutagStart(DAQ_Viewer_base):

    params = comon_parameters + [
        { 'title': 'Update Interval [s]', 'name': 'update_interval',
          'type': 'float', 'value': 1 },
        { 'title': 'Histogram bins', 'name': 'histogram_bins', 'type': 'int',
          'min': 2, 'value': 20 },
       ] + channel_settings

    live_mode_available = True

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been
            changed by the user
        """
        if param.name() == "signal_cond":
            self.controller.set_signal_conditioning(0, param.value())
        elif param.name() == "trigger_edge":
            self.controller.set_trigger_edge(0, param.value())
        elif param.name() == "trigger_threshold":
            self.controller.set_trigger_threshold(0, param.value())

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
            self.controller.open_communication()
            initialized = self.controller.initialised
        else:
            self.controller = controller
            initialized = True

        info = "Connected to quTAG"
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.close_communication()

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
                self.n_bins = self.settings['histogram_bins']
                self.controller.start_rate_zero(self.callback,
                                                self.settings['update_interval'])
            elif self.live:
                self.live = False
                self.controller.stop_rate_zero()
            return

    def callback(self, tags, dt):
        rate = len(tags) / dt
        dfp = DataFromPlugins(name='qutag', data=[rate] , dim='Data0D',
                              labels=self.channel_labels)
        self.dte_signal.emit(DataToExport(name='qutag', data=[dfp]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop_rate_zero()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG hist halted']))
        return ''


if __name__ == '__main__':
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    main(__file__)
