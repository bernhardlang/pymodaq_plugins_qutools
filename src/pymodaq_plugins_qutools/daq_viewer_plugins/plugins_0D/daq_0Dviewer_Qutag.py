import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_qutools.hardware.controller import QutagController


class DAQ_0DViewer_Qutag(DAQ_Viewer_base):
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
    params = comon_parameters+[
        { 'title': 'Report queue size', 'name': 'qsize', 'type': 'bool',
          'value': False },
        ]

    controller_type = QutagController

    live_mode_available = True

    def ini_attributes(self):
        self.controller: QutagController = None
        self.live = False

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has
            been changed by the user
        """
        if param.name() == 'qsize':
            self.controller.report_queue_size = param.value()

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

        info = "Qutag successfully initialised"
        initialized = True
        return info, initialized

    def close(self):
        self.controller.disconnect()

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
                self.live = True
                if self.settings['qsize']:
                    self.controller.start_tagging(self.send_tag_and_queue_size)
                else:
                    self.controller.start_tagging(self.send_tag)
                return
            elif self.live:
                self.live = False
                self.controller.stop_tagging()
                return

        diff = self.controller.grab_item()
        self.send_tag(diff)

    def send_tag(self, diff):
        dfp = [DataFromPlugins(name='qutag', data=[np.array([diff])],
                               dim='Data0D', labels=['diff'])]
        self.dte_signal.emit(DataToExport('qutag', data=dfp))
        
    def send_tag_and_queue_size(self, diff, qs):
        dfp = [DataFromPlugins(name='qutag', data=[np.array([diff])],
                               dim='Data0D', labels=['diff']),
               DataFromPlugins(name='qsize', data=[np.array([qs])],
                               dim='Data0D', labels=['qsize'])]
        self.dte_signal.emit(DataToExport('qutag', data=dfp))
        
    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop_tagging()
        return ''


if __name__ == '__main__':
    main(__file__)
