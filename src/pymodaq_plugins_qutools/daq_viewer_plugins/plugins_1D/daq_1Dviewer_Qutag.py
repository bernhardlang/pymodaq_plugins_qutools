import numpy as np
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.qutag_controller import QuTAGController


class DAQ_1DViewer_Qutag(DAQ_Viewer_base):

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
        # synchrone version (blocking function)
        self.controller.start_histogram(self.settings.child('channel').value(),
                                        self.callback)

    def callback(self, data):
        if self.unit == 'ns':
            data[0] *= 1e-3
        elif self.unit == 'µs':
            data[0] *= 1e-6
        dfp = DataFromPlugins(name='qutag', data=data[1], dim='Data1D',
                              labels=['channel %d' % self.channel],
                              axes=[data[0]])
        self.dte_signal.emit(DataToExport(name='qutools', data=[dfp]))


if __name__ == '__main__':
    main(__file__)
