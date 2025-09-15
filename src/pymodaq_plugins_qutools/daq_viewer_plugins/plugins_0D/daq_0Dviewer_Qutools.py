import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, \
    comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

class QuToolsInterface:

    def __init__(self):
        self.initialised = False

    def __del__(self):
        if self.initialised:
            self.qutag.deInitialize()

    def open_communication(self):
        try:
            self.qutag = QuTAG_HR.QuTAG()
        except:
            raise RuntimeError("Couldn't initialise QuTAG")
        self.initialised = True

    def close_communication(self):
        if self.initialised:
            self.qutag.deInitialize()
            self.initialised = False

    def set_signal_conditioning(self, channel, cond):
        pass

    def set_trigger_edge(self, channel, edge):
        pass

    def set_trigger_threshold(self, channel, threshold):
        pass

    def set_number_of_events(self, n_events):
        pass

    def set_number_of_bins(self, n_bins):
        pass

    def start(self, callback):
        pass
    
    def stop(self, n_bins):
        pass
    

# TODO:
# (1) change the name of the following class to DAQ_0DViewer_TheNameOfYourChoice
# (2) change the name of this file to daq_0Dviewer_TheNameOfYourChoice ("TheNameOfYourChoice" should be the SAME
#     for the class name and the file name.)
# (3) this file should then be put into the right folder, namely IN THE FOLDER OF THE PLUGIN YOU ARE DEVELOPING:
#     pymodaq_plugins_my_plugin/daq_viewer_plugins/plugins_0D

class DAQ_0DViewer_Qutools(DAQ_Viewer_base):
    """ Instrument plugin class for a quTAG OD viewer.
    """

    params = comon_parameters+[
        { 'title': 'Channel Number', 'name': 'channel', 'type': 'int',
          'min': 1, 'max': 8 },
        { 'title': 'Signal Conditioning', 'name': 'signal_cond', 'type': 'list',
          'limits': ['LVTTL', 'NIM', 'Misc'] },
        { 'title': 'Trigger Edge', 'name': 'trigger_edge', 'type': 'list',
          'limits': ['Rising', 'Falling'] },
        { 'title': 'Trigger Threshold', 'name': 'trigger_threshold',
          'type': 'float', 'min': -2, 'max': 3 },
        { 'title': 'Histogram Events', 'name': 'events', 'type': 'int',
          'min': 1, },
        { 'title': 'Histogram Bins', 'name': 'bins', 'type': 'int', 'min': 1, },
        ]

    def ini_attributes(self):
        self.controller: QuToolsInterface = None
        self.channel = 1

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == "channel":
            self.channel = channel
        if param.name() == "events":
            self.controller.set_number_of_events(param.value())
        if param.name() == "bins":
            self.controller.set_number_of_bins(param.value())
        elif param.name() == "signal_cond":
           self.controller.set_signal_conditioning(self.channel, param.value())
        elif param.name() == "trigger_edge":
           self.controller.set_trigger_edge(self.channel, param.value())
        elif param.name() == "trigger_threshold":
           self.controller.set_trigger_threshold(self.channel, param.value())
        ##

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one
            actuator/detector by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:
            self.controller = QuToolsInterface()
            self.controller.open_communication()
            initialized = self.controller.is_initialised()
        else:
            self.controller = controller
            initialized = True

        dfp = DataFromPlugins(name='qutag', data=[np.array([0]), np.array([0])],
                              dim='Data0D', labels=['mean', 'sigma'])
        self.dte_signal_temp.emit(DataToExport(name='qutag', data=[dfp]))

        info = "Connected to quTAG"
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.close_communication()

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
        # synchrone version (blocking function)
        self.controller.start(self.callback)

    def callback(self, data):
        dfp = DataFromPlugins(name='qutag', data=data, dim='Data0D',
                              labels=['mean', 'sigma'])
        self.dte_signal.emit(DataToExport(name='qutools', data=[dfp]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop()
        self.emit_status(ThreadCommand('Update_Status', ['quTAG halted']))
        return ''


if __name__ == '__main__':
    main(__file__)
