from pymodaq.control_modules.viewer_utility_classes import main
from pymodaq_plugins_qutools.daq_viewer_plugins.plugins_1D \
    .daq_1Dviewer_Qutag_hist import DAQ_1DViewer_Qutag_hist
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_qutools.hardware.controller import QutagController, \
    QutagControllerSimu

#from pymodaq.utils.daq_utils import ThreadCommand
#from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport


class DAQ_1DViewer_Qutag_hist_simu(DAQ_1DViewer_Qutag_hist):
    """ Instrument plugin class for a 1D viewer.

    This object inherits all functionalities to communicate with PyMoDAQ’s
    DAQ_Viewer module through inheritance via DAQ_Viewer_base. It makes a
    bridge between the DAQ_Viewer module and the Python wrapper of a
    particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of instruments that should be compatible with this
         instrument plugin.
        * With which instrument it has actually been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be
          installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware,
        in general a python wrapper around the hardware library.
         
    # TODO add your particular attributes here if any

    """
    hw_params = [
        { 'title': 'Number of bins', 'name': 'n_bins', 'type': 'int', 'min': 1,
          'value': 100 },
        { 'title': 'Histogram start', 'name': 'start_hist', 'type': 'float',
          'min': -1e-3, 'max': 1e-3, 'value': -2e-6 },
        { 'title': 'Histogram end', 'name': 'end_hist', 'type': 'float',
          'min': -1e-3, 'max': 1e-3, 'value': 2e-6 },
        ]
#    params = daq_1Dviewer_Qutag_hist.params

    controller_type = QutagControllerSimu


if __name__ == '__main__':
    main(__file__)
