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

    def ini_attributes(self):
        self.controller: QuTAGController = None
        self.live = False

    def callback(self, tags, dt):
        self.n_bins = self.settings['n_bins']
        self.hist_ps = Histogram(self.n_bins)
        self.hist_fs = Histogram(self.n_bins)
        self.hist_diff = Histogram(self.n_bins)

        while True:
            # skip tags before start event on channel 0
            while self.idx < n_tt and self.time_tags[self.idx][1]:
                self.idx += 1

            if self.idx > n_tt - 4: # over?
                break
    
            start = self.time_tags[self.idx][0]
            self.idx += 1
            self.tags_on_channel.fill(-1)

            for _ in range(3):
                tag = self.time_tags[self.idx][0] - start
                channel = int(self.time_tags[self.idx][1] - 1)
                if tag < 1000:
                    self.tags_on_channel[channel] = tag
                self.idx += 1

            if self.standalone or self.tags_on_channel[2] > 0:
                self.hist_ps.collect(self.tags_on_channel[0])
                self.hist_fs.collect(self.tags_on_channel[1])
                self.hist_diff.collect(self.tags_on_channel[1]
                                       - self.tags_on_channel[0])

        self.time_tags = self.time_tags[self.idx:]
        self.idx = 0

        dfp0 = DataFromPlugins(name='qutag', data=self.hist_ps.bins,
                               dim='Data1D', labels=['ch 0'],
                               axes=[Axis(data=self.hist_ps.centers,
                                          label='', units='', index=0)])
        dfp1 = DataFromPlugins(name='qutag', data=self.hist_fs.bins,
                               dim='Data1D', labels=['ch 1'],
                               axes=[Axis(data=self.hist_fs.centers,
                                          label='', units='', index=0)])
        dfp_diff = DataFromPlugins(name='qutag', data=self.hist_diff.bins,
                                   dim='Data1D', labels=['difference'],
                                   axes=[Axis(data=self.hist_diff.centers,
                                              label='', units='', index=0)])
        self.dte_signal.emit(DataToExport(name='qutag',
                                          data=[dfp0, dfp1, dfp_diff]))


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
