import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.common QutagCommon
from pymodaq_plugins_qutools.histogram Histogram


class DAQ_1DViewer_QutagTA(QutagCommon, DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG 1D viewer in picosecond TA experiment.
    """

    params = [
        { 'title': 'Excitation laser', 'name': 'excitation', 'type': 'int',
          'min': 1, 'max': 8, 'value': 1 },
        { 'title': 'Probe laser', 'name': 'probe', 'type': 'int',
          'min': 1, 'max': 8, 'value': 1 },
        { 'title': 'Histogram bins', 'name': 'n_bins', 'type': 'int',
          'min': 2, 'value': 100 },
       ] + QutagCommon.params

    controller_type = TAQuTAGController

    def ini_attributes(self):
        self.controller: TAQuTAGController = None
        self.live = False

    def callback(self, items):
        self.n_bins = self.settings['n_bins']
        self.hist_ps = Histogram(self.n_bins)
        self.hist_fs = Histogram(self.n_bins)
        self.hist_diff = Histogram(self.n_bins)

        for item in items:
            self.hist_ps.add(item[0])
            self.hist_fs.add(item[1])
            self.hist_diff.add(item[1] - item[0])

        excitation = DataFromPlugins(name='qutag', data=self.hist_ps.bins,
                                     dim='Data1D', labels=['ch 0'],
                                     axes=[Axis(data=self.hist_ps.centers,
                                                label='', units='', index=0)])
        probe = DataFromPlugins(name='qutag', data=self.hist_fs.bins,
                                dim='Data1D', labels=['ch 1'],
                                axes=[Axis(data=self.hist_fs.centers,
                                           label='', units='', index=0)])
        diff = DataFromPlugins(name='qutag', data=self.hist_diff.bins,
                               dim='Data1D', labels=['difference'],
                               axes=[Axis(data=self.hist_diff.centers,
                                          label='', units='', index=0)])
        self.dte_signal.emit(DataToExport(name='qutag',
                                          data=[excitation, probe, diff]))


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
