from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.hardware.controller import MockQuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_1D.daq_1Dviewer_Qutag \
    import DAQ_1DViewer_Qutag


class DAQ_1DViewer_MockPsQutag(DAQ_1DViewer_Qutag):
    """ Instrument plugin class for a simulated quTAG 1D viewer.
    """

    params = DAQ_1DViewer_Qutag.params + [
        { 'title': 'Rate [1/s]', 'name': 'rate', 'type': 'float', 'min': 1,
          'value': 1e3 },
        { 'title': 'Delay [s]', 'name': 'delay', 'type': 'float',
          'min': 0, 'value': 1e-4 },
        { 'title': 'Jitter [s]', 'name': 'jitter', 'type': 'float',
          'min': 0, 'value': 1e3 },
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
            channel = 0 if self.controller.lifetimes[self._channel] \
                else self._channel
            self.controller.rates[channel] = param.value()
        elif param.name() == "delay":
            self.controller.delays[self.settings['channel']] = param.value()
        elif param.name() == "jitter":
            self.controller.jitter[self.settings['channel']] = param.value()
        else:
            super().commit_settings(param)

    def _set_params(self):
        super()._set_params()
        self.controller.lifetimes[self._channel] = self.settings['lifetime']
        channel = 0 if self.settings['lifetime'] else self._channel
        self.controller.rates[channel] = self.settings['rate']
            
    @property
    def _external_trigger(self):
        return self.settings['lifetime'] > 0


if __name__ == '__main__':
    main(__file__)
