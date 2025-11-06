import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.qutag_controller import QuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.common.qutag_common \
    import QutagCommon, Histogram


class DAQ_1DViewer_Qutag(QutagCommon, DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG 1D viewer.
    """

    params = comon_parameters + QutagCommon.common_parameters \
        + [{ 'title': 'Use channel one as start', 'name': 'ch_one_as_start',
             'type': 'bool', 'value': False },
           { 'title': 'Histogram bins', 'name': 'histogram_bins', 'type': 'int',
             'min': 2, 'value': 20 },
           ]

    def ini_attributes(self):
        self.controller: QuTAGController = None
        self.n_bins = 20
        self.live = False

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
        if not self.controller.collecting_events: # first call?
            channels = self.determine_active_channels()
            self.channel_labels = ['channel %d' % c for c in channels]

        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                update_interval = self.settings.child("update_interval").value()
                self.ch_one_as_start = \
                    self.settings.child("ch_one_as_start").value()
                self.n_bins = self.settings.child("histogram_bins").value()
                self.start_tag = 0
                self.controller.start_events(channels, self.callback,
                                             update_interval,
                                             not self.ch_one_as_start)
            elif self.live:
                self.live = False
                self.controller.stop_events()
            return

        if not self.controller.collecting_events:
            self.controller.start_events(channels)
            return

        time_tags = self.controller.grab_time_tags()
        self.callback(time_tags)

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
                dfp = DataFromPlugins(name='qutag', data=hist.bins,
                                      dim='Data1D',
                                      labels=[self.channel_labels[channel]],
                                      axes=[Axis(data=hist.centers, label='',
                                                 units='', index=0)])
                data.append(dfp)

        self.dte_signal.emit(DataToExport(name='qutag', data=data))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop_events()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG hist halted']))
        return ''


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
