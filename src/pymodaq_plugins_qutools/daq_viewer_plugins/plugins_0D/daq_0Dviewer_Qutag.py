import numpy as np
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.qutag_controller import QuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.common.qutag_common \
    import QutagCommon


class DAQ_0DViewer_Qutag(QutagCommon, DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG OD viewer.
    """

    params = comon_parameters + QutagCommon.common_parameters

    def ini_attributes(self):
        self.controller: QuTAGController = None

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
        if not self.controller.measuring_rates:
            channels = self.determine_active_channels()
#            if len(channels) == 8:
#                channels = channels[:-1]
            self.channel_labels = ['channel %d' % c for c in channels]

        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                update_interval = self.settings.child("update_interval").value()
                self.controller.start_rates(channels, self.callback,
                                            update_interval)
            elif self.live:
                self.live = False
                self.controller.stop_rates()
            return

        if not self.controller.measuring_rates:
            self.controller.start_rates(channels)
            return

        rates = self.controller.grab_rates()
        self.callback(rates)

    def callback(self, data):
#        if len(data) == 8:
#            data = data[:-1]
        dfp = DataFromPlugins(name='qutag', data=data, dim='Data0D',
                              labels=self.channel_labels)
        self.dte_signal.emit(DataToExport(name='qutag', data=[dfp]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop_rates()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG rate halted']))
        return ''


if __name__ == '__main__':
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    main(__file__, init_h5=False)
