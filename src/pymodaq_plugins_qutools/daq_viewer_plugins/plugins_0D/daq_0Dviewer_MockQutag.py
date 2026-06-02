from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_0D.daq_0Dviewer_Qutag \
    import DAQ_0DViewer_Qutag


class DAQ_0DViewer_MockQutag(DAQ_0DViewer_Qutag):

    params = DAQ_0DViewer_Qutag.params + [
        { 'title': 'Rate [1/s]', 'name': 'rate', 'type': 'float', 'min': 1,
          'value': 1e5 },
        ]

    controller_type = MockQuTAGController

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
        else:
            super().commit_settings(param)


if __name__ == '__main__':
#    from PyQt5.QtCore import pyqtRemoveInputHook
#    pyqtRemoveInputHook()
    main(__file__)
