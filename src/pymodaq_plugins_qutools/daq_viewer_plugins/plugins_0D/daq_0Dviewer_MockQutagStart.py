from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_0D.\
    daq_0Dviewer_QutagStart import DAQ_0DViewer_QutagStart
from pymodaq_plugins_qutools.hardware.controller import MockQuTAGController


class DAQ_0DViewer_MockQutagStart(DAQ_0DViewer_QutagStart):

    params = DAQ_0DViewer_QutagStart.params + [
        { 'title': 'Rate [1/s]', 'name': 'rate', 'type': 'float', 'min': 1,
          'value': 1e5 },
        ]
    
    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been
            changed by the user
        """
        if param.name() == "rate":
            self.controller.rates[0] = param.value()

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = MockQuTAGController()
            self.controller.open_communication()
            initialized = self.controller.initialised
        else:
            self.controller = controller
            initialized = True

        info = "Connected to quTAG"
        return info, initialized


if __name__ == '__main__':
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    main(__file__)
