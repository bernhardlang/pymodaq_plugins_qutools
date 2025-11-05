import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.hardware.qutag_controller import QuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.common.qutag_common \
    import QutagCommon


class DAQ_1DViewer_Qutag(QutagCommon, DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG 1D viewer.
    """

    params = comon_parameters + QutagCommon.common_parameters \
        + [{ 'title': 'Use channel one as start', 'name': 'start_one_',
             'type': 'bool', 'value': False },
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
                self.controller.start_events(channels, self.callback,
                                             update_interval)
            elif self.live:
                self.live = False
                self.controller.stop_events()
            return

        if not self.controller.collecting_events:
            self.controller.start_events(channels)
            return

        time_tags = self.controller.grab_time_tags()
        self.callback(time_tags)

    def callback(self, time_tags):
        data = []
        if self.settings.child('calculate_difference').value():
            n_tags = min(len(time_tags[0]), len(time_tags[1]))
            diff = np.empty(n_tags)
            for i in range(n_tags):
                diff[i] = time_tags[1][i] - time_tags[0][i]
            time_tags.append(diff)

        for channel,tags in enumerate(time_tags):
            if not len(tags):
                continue
            min_val = min(tags)
            max_val = max(tags)
            bin_size = (max_val - min_val) / self.n_bins
            centers = np.linspace(min_val + 0.5 * bin_size,
                                  max_val - 0.5 * bin_size, self.n_bins)
            bins = np.zeros(self.n_bins)
            for tag in tags:
                idx = int((tag - min_val) / bin_size)
                if idx >= 0 and idx < self.n_bins:
                    bins[idx] += 1
            try:
                label = self.channel_labels[channel]
            except:
                label = 'difference'

            dfp = DataFromPlugins(name='qutag', data=bins, dim='Data1D',
                                  labels=[label],
                                  axes=[Axis(data=centers, label='', units='',
                                             index=0)])
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
