import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_qutools.hardware.controller import QutagController


class DAQ_1DViewer_Qutag_hist(DAQ_Viewer_base):
    """ Instrument plugin class for a 1D viewer of a quTAG device from
        qutools https://qutools.com/qutag-hr

    Tested on verion 2 of the device using python 3.10.14 and
    PyMoDAQ 4.3.x_dev under Debian 12.5
    Needed are library libtdcbase.so / tdcbase.dll and the file
    QuTAG_HR.py in the python examples provided py qutools. Copy both latter
    into the hardware directory.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware,
        in general a python wrapper around the hardware library.
         
    # TODO add your particular attributes here if any

    """
    hw_params = [
        { 'title': 'Number of bins', 'name': 'n_bins', 'type': 'int', 'min': 1,
          'value': 100 },
        { 'title': 'Histogram start', 'name': 'hist_start', 'type': 'float',
          'min': -1e-3, 'max': 1e-3, 'value': -1e-5 },
        { 'title': 'Histogram end', 'name': 'hist_end', 'type': 'float',
          'min': -1e-3, 'max': 1e-3, 'value': 1e-5 },
        ]

    params = comon_parameters+hw_params+[
        { 'title': 'Acquisition time (s)', 'name': 'acqisition_time',
          'type': 'float', 'min': 1e-3, 'max': 10, 'value': 1 },
        ]

    hw_param_names = [param['name'] for param in hw_params]

    controller_type = QutagController

    def ini_attributes(self):
        self.controller: QutagController = None

        # TODO declare here attributes you want/need to init with a default
        # value

        self.x_axis = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has
            been changed by the user
        """
        if param.name() in self.hw_param_names:
            setattr(self.controller, param.name(), param.value())
            self.controller.update_hist()
            self.emit_axis()

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only
            one actuator/detector by controller(Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        self.ini_detector_init(old_controller=controller,
                               new_controller=self.controller_type())

        if self.is_master:
            self.controller.connect()

        for name in self.hw_param_names:
            setattr(self.controller, name, self.settings[name])
        self.controller.update_hist()
        self.emit_axis()

        info = "Qutag successfully initialised"
        initialized = True
        return info, initialized

    def close(self):
        self.controller.disconnect()

    def emit_axis(self):
        step = self.controller.hist_step
        data_x_axis = np.linspace(self.controller.hist_start + 0.5 * step,
                                  self.controller.hist_end - 0.5 * step,
                                  self.controller.n_bins)
        self.x_axis = Axis(data=data_x_axis, label='', units='', index=0)

        dfp = [DataFromPlugins(name='qutag',
                               data=[np.zeros(self.controller.n_bins)],
                               dim='Data1D', labels=['hist'],
                               axes=[self.x_axis])]
        self.dte_signal_temp.emit(DataToExport(name='qttag', data=dfp))

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
        hist = self.controller.grab_hist(self.settings['acqisition_time'])
        dfp = [DataFromPlugins(name='qutag', data=hist, dim='Data1D',
                               labels=['hist'], axes=[self.x_axis])]
        self.dte_signal.emit(DataToExport('qutag', data=dfp))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__)
