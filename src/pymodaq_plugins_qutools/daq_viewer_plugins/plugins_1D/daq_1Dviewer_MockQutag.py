from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_1D.daq_1Dviewer_Qutag \
    import DAQ_1DViewer_Qutag
from pymodaq_plugins_qutools.hardware.controller import MockQuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.common.qutag_common \
    import QutagCommonHistogram, Histogram


class DAQ_1DViewer_MockQutag(DAQ_1DViewer_Qutag):
    """ Instrument plugin class for a simulated quTAG 1D viewer.
    """

    params = DAQ_0DViewer_Qutag.params + [
        { 'title': 'Rate [1/s]', 'name': 'rate', 'type': 'float', 'min': 1,
          'value': 1e5 },
        ]

    params = comon_parameters + [
        { 'title': 'Channel', 'name': 'channel', 'type': 'int', 'min': 1,
          'max': 8, 'value': 1 },
        { 'title': 'Update Interval [s]', 'name': 'update_interval',
          'type': 'float', 'value': 1 },
        { 'title': 'Histogram bins', 'name': 'n_bins', 'type': 'int', 'min': 1,
          'value': 10 },
       ] + channel_settings

    simulate = True

    def ini_attributes(self):
        self.controller: MockQuTAGController = None
        self.live = False

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = MockQuTAGController()
            update_interval = self.settings.child('update_interval').value()
            self.controller.open_communication(update_interval)
            initialized = self.controller.initialised
            for i in range(9):
                self.controller.rates = \
                    [self.settings.child('rates').child(f'rate_{i}').value()
                     for i in range(9)]
        else:
            self.controller = controller
            initialized = True

        return "MockQutag plugin initialised", initialized
            

if __name__ == '__main__':
    #from qtpy.QtCore import pyqtRemoveInputHook
    #pyqtRemoveInputHook() # to be able to use pdb inside Qt's event loops
    main(__file__)
