import numpy as np
from pymodaq_data.data import DataToExport
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.common import QutagCommon
from pymodaq_plugins_qutools.hardware.controller import QuTAGController, \
    MockQuTAGController, channel_settings


class DAQ_0DViewer_Qutag(QutagCommon):
    """ Instrument plugin class for a quTAG OD viewer.
    """

    def ini_attributes(self):
        self.controller: QuTAGController = None

    def callback(self, data, dt):
        rate = len(data) / dt
        dfp = DataFromPlugins(name='qutag', data=[np.array([rate])],
                              dim='Data0D',
                              labels=[f'Ch {self.settings['channel']}'])
        self.dte_signal.emit(DataToExport(name='qutag', data=[dfp]))


if __name__ == '__main__':
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    main(__file__)
