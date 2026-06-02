import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.common import QutagCommon
from pymodaq_plugins_qutools.hardware.controller import QuTAGController, \
    MockQuTAGController, channel_settings


class DAQ_0DViewer_QutagStart(QutagCommon):

    controller_type = QuTAGController

    @property
    def _channel(self):
        return 0

    def callback(self, tags, dt):
        rate = len(tags) / dt
        dfp = DataFromPlugins(name='qutag', data=[np.array([rate])],
                              dim='Data0D', labels=[f'Start'])
        self.dte_signal.emit(DataToExport(name='qutag', data=[dfp]))


if __name__ == '__main__':
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    main(__file__)
