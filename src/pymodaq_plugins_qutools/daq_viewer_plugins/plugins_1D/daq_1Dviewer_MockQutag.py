from daq_1Dviewer_Qutag.py import DAQ_1DViewer_Qutag
from pymodaq_plugins_qutools.hardware.qutag_controller import MockQuTAGController

class DAQ_1DViewer_MockQutag(DAQ_1DViewer_Qutag):
    """ Instrument plugin class for a simulated quTAG 1D viewer.
    """

    params = QutagCommonHistogram.params \
        + [{ 'title': 'Use channel one as start', 'name': 'ch_one_as_start',
             'type': 'bool', 'value': False },
           ]

    def ini_attributes(self):
        self.controller: MockQuTAGController = None
        self.live = False

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = MockQuTAGController()
            update_interval = self.settings.child('update_interval').value()
            self.controller.open_communication(update_interval)
            initialized = self.controller.is_initialised()
        else:
            self.controller = controller
            initialized = True


if __name__ == '__main__':
    from PyQt6.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
