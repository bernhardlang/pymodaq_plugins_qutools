from pymodaq_gui.parameter import Parameter
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.hardware.controller import MockQuTAGController
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_1D.daq_1Dviewer_QutagTA \
    import DAQ_1DViewer_QutagTA
from pymodaq_plugins_qutools.hardware.controller import MockTAQuTAGController


class DAQ_1DViewer_MockPsQutag(DAQ_1DViewer_QutagTA):
    """ Instrument plugin class for a simulated quTAG 1D viewer.
    """

    params = DAQ_1DViewer_QutagTA.params + [
        { 'title': 'Rate [1/s]', 'name': 'rate', 'type': 'float', 'min': 1,
          'value': 1e3 },
        { 'title': 'Delay [s]', 'name': 'delay', 'type': 'float',
          'min': 0, 'value': 1e-4 },
        { 'title': 'Jitter [s]', 'name': 'jitter', 'type': 'float',
          'min': 0, 'value': 1e3 },
        ]

    controller_type = MockTAQuTAGController

    def ini_attributes(self):
        self.controller: MockQuTAGController = None
        self.live = False

    def _set_params(self):
        super()._set_params()
        trigger_rate = self.settings['rate']
        self.controller.trigger_rate = trigger_rate
        self.controller.excitation_laser = \
            1 / (2 * trigger_rate) - self.settings['delay'] - 60e-6
        self.controller.excitation_jitter = self.settings['jitter']

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG rate halted']))
        return ''

if __name__ == '__main__':
    main(__file__)
