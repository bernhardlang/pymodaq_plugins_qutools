from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_0D.\
    daq_0Dviewer_QutagStart import DAQ_0DViewer_QutagStart


class DAQ_0DViewer_MockQutagStart(DAQ_0DViewer_QutagStart):

    params = DAQ_0DViewer_QutagStart.params + [
        { 'title': 'Rate [1/s]', 'name': 'rate', 'type': 'float', 'min': 1,
          'value': 1e5 },
        { 'title': 'External trigger', 'name': 'ext_trig', 'type': 'bool',
          'default': False }
        ]
    
    simulate = True

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
        elif param.name() == "ext_trig":
            self.controller.external_trigger = param.value()
        else:
            super().commit_settings(param)


if __name__ == '__main__':
#    from PyQt5.QtCore import pyqtRemoveInputHook
#    pyqtRemoveInputHook()
    main(__file__)
