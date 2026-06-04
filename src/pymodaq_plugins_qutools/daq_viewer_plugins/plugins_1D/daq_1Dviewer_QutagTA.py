import numpy as np
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_utils.utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools.common import QutagCommon
from pymodaq_plugins_qutools.histogram import Histogram
from pymodaq_plugins_qutools.hardware.controller import TAQuTAGController


class DAQ_1DViewer_QutagTA(QutagCommon):
    """ Instrument plugin class for a quTAG 1D viewer in picosecond TA experiment.
    """

    params = [
        { 'title': 'Excitation laser', 'name': 'excitation', 'type': 'int',
          'min': 1, 'max': 8, 'value': 1 },
        { 'title': 'Probe laser', 'name': 'probe', 'type': 'int',
          'min': 1, 'max': 8, 'value': 2 },
        { 'title': 'Histogram bins', 'name': 'n_bins', 'type': 'int',
          'min': 2, 'value': 100 },
       ] + QutagCommon.params

    controller_type = TAQuTAGController

    def ini_attributes(self):
        self.controller: TAQuTAGController = None
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
        if 'live' in kwargs:
            if kwargs['live']:
                self._set_params()
                self.live = True
                self.controller.start(self.settings['excitation'],
                                      self.settings['probe'], self.callback,
                                      self.settings['update_interval'])
            elif self.live:
                self.live = False
                self.controller.stop(self._channel)

    def callback(self, excitation, probe):
        n_bins = self.settings['n_bins']
        hist_ps = Histogram(n_bins, excitation)
        hist_fs = Histogram(n_bins, probe)
        hist_diff = Histogram(n_bins, [p - e for p,e in zip(excitation, probe)])

        excitation_data = DataFromPlugins(name='qutag', data=hist_ps.bins,
                                          dim='Data1D', labels=['ch 0'],
                                          axes=[Axis(data=hist_ps.centers,
                                                   label='', units='', index=0)])
        probe_data = DataFromPlugins(name='qutag', data=hist_fs.bins,
                                     dim='Data1D', labels=['ch 1'],
                                     axes=[Axis(data=hist_fs.centers,
                                                label='', units='', index=0)])
        diff_data = DataFromPlugins(name='qutag', data=hist_diff.bins,
                                    dim='Data1D', labels=['difference'],
                                    axes=[Axis(data=hist_diff.centers,
                                               label='', units='', index=0)])
        self.dte_signal.emit(DataToExport(name='qutag',
                                          data=[excitation_data, probe_data,
                                                diff_data]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG rate halted']))
        return ''


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
