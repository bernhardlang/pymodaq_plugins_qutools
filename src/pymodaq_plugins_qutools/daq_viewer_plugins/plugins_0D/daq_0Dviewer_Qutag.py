import numpy as np
from pymodaq_data.data import DataToExport
from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq.utils.data import DataFromPlugins
from pymodaq_plugins_qutools\
    .daq_viewer_plugins.plugins_0D.daq_0Dviewer_QutagStart \
    import DAQ_0DViewer_QutagStart
from pymodaq_plugins_qutools.common import QutagCommon
from pymodaq_plugins_qutools.hardware.controller import QuTAGController, \
    MockQuTAGController, channel_settings


class DAQ_0DViewer_Qutag(DAQ_0DViewer_QutagStart):
    """ Instrument plugin class for a quTAG OD viewer.
    """

    params = [
        { 'title': 'Channel', 'name': 'channel', 'type': 'int', 'min': 1,
          'max': 8, 'value': 1 },
        ] + QutagCommon.params

    controller_type = QuTAGController

if __name__ == '__main__':
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    main(__file__)
