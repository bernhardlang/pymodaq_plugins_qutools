import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.controller import QuTAGController
from pymodaq_plugins_qutools.common import QutagCommon
from pymodaq_plugins_qutools.histogram import Histogram


class DAQ_1DViewer_Qutag(QutagCommon):
    """ Instrument plugin class for a quTAG 1D viewer.
    """

    params = [
        { 'title': 'Channel', 'name': 'channel', 'type': 'int', 'min': 1,
          'max': 8, 'value': 1 },
        { 'title': 'Histogram bins', 'name': 'n_bins', 'type': 'int',
          'min': 2, 'value': 100 },
        ] + QutagCommon.params

    controller_type = QuTAGController

    def callback(self, tags, dt):
        hist = Histogram(self.n_bins, tags)
        dfp = DataFromPlugins(name='qutag', data=hist.bins, dim='Data1D',
                              labels=[f'Ch {self._channel}'],
                              axes=[Axis(data=hist.centers, label='',
                                         units='', index=0)])
        self.dte_signal.emit(DataToExport(name='qutag', data=[dfp]))

    def _set_params(self):
        self.n_bins = self.settings['n_bins']


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
