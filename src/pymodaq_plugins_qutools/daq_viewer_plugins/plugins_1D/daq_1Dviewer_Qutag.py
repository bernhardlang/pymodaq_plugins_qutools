import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.qutag_controller import QuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.common.qutag_common \
    import QutagCommonHistogram, Histogram


class DAQ_1DViewer_Qutag(QutagCommonHistogram, DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG 1D viewer.
    """

    params = QutagCommonHistogram.params \
        + [{ 'title': 'Use channel one as start', 'name': 'ch_one_as_start',
             'type': 'bool', 'value': False },
           ]

    def ini_attributes(self):
        self.controller: QuTAGController = None
        self.live = False

    def start_live(self):
        self.start_tag = 0
        self.ch_one_as_start = self.settings.child("ch_one_as_start").value()
        return not self.ch_one_as_start

    def callback(self, incoming_tags):
        data = []

        if self.ch_one_as_start:
            hists = [Histogram(self.n_bins)
                     for _ in range(len(self.channel_labels))]
            for tag in incoming_tags:
                channel = int(tag[1])
                if not channel:
                    self.start_tag = tag[0]
                else:
                    hists[channel].collect(tag[0] - self.start_tag)

            for i,hist in enumerate(hists):
                if not hist.samples:
                    continue
                dfp = DataFromPlugins(name='qutag', data=hist.bins,
                                      dim='Data1D',
                                      labels=[self.channel_labels[i]],
                                      axes=[Axis(data=hist.centers, label='',
                                                 units='', index=0)])
                data.append(dfp)
        else:
            for channel,tags in enumerate(incoming_tags):
                if not len(tags):
                    continue
                hist = Histogram(self.n_bins, tags)
                try:
                    dfp = DataFromPlugins(name='qutag', data=hist.bins,
                                          dim='Data1D',
                                          labels=[self.channel_labels[channel]],
                                          axes=[Axis(data=hist.centers, label='',
                                                     units='', index=0)])
                except:
                    import pdb
                    pdb.set_trace()
                data.append(dfp)

        self.dte_signal.emit(DataToExport(name='qutag', data=data))


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
