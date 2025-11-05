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

class Histogram:

    def __init__(self, n_bins, min_val=None, max_val=None):
        self.n_bins = n_bins
        if min_val is not None:
            self.set_up(min_val, max_val, n_bins)
            self._changed = False
            self.values = None
        else:
            self.values = []

    def set_up(self, min_val, max_val):
        self._centers = np.linspace(min_val, max_val, self.n_bins)
        self.bin_width = self._centers[1] - self._centers[0]
        try:
            assert self.bin_width
        except:
            import pdb
            pdb.set_trace()
        self.ranges = \
            np.linspace(min_val - self.bin_width, max_val + self.bin_width,
                        self.n_bins + 1)
        self._bins = np.zeros(self.n_bins)
        self.start_range = self.ranges[0]
        self._changed = True

    def _set_up(self):
        if not len(self.values):
            return
        self.set_up(min(self.values), max(self.values))
        for value in self.values:
            self.add(value)

    def add(self, value):
        idx = int((value - self.start_range) / self.bin_width)
        if idx >= 0:
            try:
                self._bins[idx] += 1
            except:
                pass

    def collect(self, value):
        self.values.append(value)

    @property
    def bins(self):
        if not hasattr(self, '_bins'):
            self._set_up()
            self._update()
        return self._bins

    @property
    def centers(self):
        if not hasattr(self, '_centers'):
            self._set_up()
            self._update()
        return self._centers

    @property
    def samples(self):
        if self._changed:
            self._update()
        return self._samples

    @property
    def mean(self):
        if self._changed:
            self._update()
        return self._mean
    
    @property
    def sigma(self):
        if self._changed:
            self._update()
        return self._sigma

    @property
    def normalised_bins(self):
        if self._changed:
            self._update()
        return self._normalised_bins

    def _update(self):
        if not hasattr(self, '_bins'):
            self._set_up()
        self._samples = sum(self._bins)
        self._normalised_bins = self._bins / (self._samples * self.bin_width)
        self._mean = \
            np.dot(self._normalised_bins, self._centers) * self.bin_width
        self._sigma = \
            np.sqrt(np.dot(self._normalised_bins,
                           (self._centers - self._mean)**2) * self.bin_width)
        self._changed = False

    
class DAQ_1DViewer_QutagTA(QutagCommon, DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG 1D viewer.
    """

    params = comon_parameters + QutagCommon.common_parameters \
     + [{ 'title': 'Stand-alone', 'name': 'standalone', 'type': 'bool',
          'value': True },
        { 'title': 'Histogram bins', 'name': 'n_bins',
          'type': 'bool', 'value': True },
        { 'title': 'Calculate difference', 'name': 'calculate_difference',
          'type': 'bool', 'value': True },
       ]

    time_tags_per_channel = False

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

        self.standalone = self.settings.child("standalone").value()
        self.calculate_difference = \
            self.settings.child('calculate_difference').value()
        self.time_tags = []
        self.idx = 0
        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                update_interval = self.settings.child("update_interval").value()
                self.time_tags = []
                self.tags_on_channel = np.empty(3)
                self.increment = 3 if self.standalone else 5
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

    def callback(self, incoming_time_tags):
        """
        stand-alone operation (without CCD):
        sequence 1: PD ps, PD fs, PD fs -> ch 0, 1, 1
        sequence 2: PD fs, PD ps, PD fs -> ck 1, 0, 1
        - identfy event on channel 0
        - check delay to event on channel 1 after
        - delay > 900µs ? take event on channel 1 before : after

        normal operation (with CCD):
        sequence 1: PD ps, PD fs, XCK, PD fs -> ch 0, 1, 2, 1
        sequence 2: PD fs, PD ps, XCK, PD fs -> ck 1, 0, 2, 1
        - identfy event on channel 2
        - take events on channel 0 and 1 before
        """

        self.time_tags = self.time_tags + incoming_time_tags
        n_tt = len(self.time_tags)
        self.hist0 = Histogram(20)
        self.hist1 = Histogram(20)
        self.hist_diff = Histogram(20)

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
                self.hist0.collect(self.tags_on_channel[0])
                self.hist1.collect(self.tags_on_channel[1])
                if self.calculate_difference:
                    self.hist_diff.collect(self.tags_on_channel[1]
                                           - self.tags_on_channel[0])
                
        self.time_tags = self.time_tags[self.idx:]
        self.idx = 0

        dfp0 = DataFromPlugins(name='qutag', data=self.hist0.bins,
                               dim='Data1D', labels=['ch 0'],
                               axes=[Axis(data=self.hist0.centers,
                                          label='', units='', index=0)])
        dfp1 = DataFromPlugins(name='qutag', data=self.hist1.bins,
                               dim='Data1D', labels=['ch 1'],
                               axes=[Axis(data=self.hist1.centers,
                                          label='', units='', index=0)])
        dfp_diff = DataFromPlugins(name='qutag', data=self.hist_diff.bins,
                                   dim='Data1D', labels=['difference'],
                                   axes=[Axis(data=self.hist_diff.centers,
                                              label='', units='', index=0)])
        self.dte_signal.emit(DataToExport(name='qutag',
                                          data=[dfp0, dfp1, dfp_diff]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop_events()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG hist halted']))
        return ''


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
