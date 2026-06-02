from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.hardware.controller import MockQuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_1D.daq_1Dviewer_Qutag \
    import DAQ_1DViewer_Qutag


class DAQ_1DViewer_MockQutag(DAQ_1DViewer_Qutag):
    """ Instrument plugin class for a simulated quTAG 1D viewer.
    """

    params = DAQ_1DViewer_Qutag.params + [
        { 'title': 'Rate [1/s]', 'name': 'rate', 'type': 'float', 'min': 1,
          'value': 1e5 },
        { 'title': 'Lifetime [1/s]', 'name': 'lifetime', 'type': 'float',
          'min': 0, 'value': 1, 'default': 0 },
        ]

    simulate = True

    def ini_attributes(self):
        self.controller: MockQuTAGController = None
        self.live = False

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been
            changed by the user
        """
        if param.name() == "rate":
            self.controller.rates[self.settings['channel']] = param.value()
        else:
            super().commit_settings(param)

    def ini_detector(self, controller=None):
        if self.is_master:
            self.controller = MockQuTAGController()
            self.controller.open_communication()
            initialized = self.controller.initialised
        else:
            self.controller = controller
            initialized = True

        return "MockQutag plugin initialised", initialized
            

if __name__ == '__main__':
    main(__file__)
