import numpy as np
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QMainWindow, QWidget, QApplication, QProgressBar, \
    QFileDialog, QMenuBar # <<--
from pymodaq.control_modules.daq_viewer import DAQ_Viewer
from pymodaq_utils.config import Config
from pymodaq_utils.logger import set_logger, get_module_name
from pymodaq.utils.data import DataToExport, DataFromPlugins, DataWithAxes
from pymodaq_gui import utils as gutils
from pymodaq_gui.utils.dock import DockArea, Dock
from pymodaq_gui.utils.main_window import MainWindow
from pymodaq_gui.plotting.data_viewers.viewer1D import Viewer1D, Viewer0D
from pymodaq_plugins_qutools.utils import Config as PluginConfig

logger = set_logger(get_module_name(__file__))

main_config = Config()
plugin_config = PluginConfig()


class QuTAGApp(gutils.CustomApp):

    params = []

    def __init__(self, parent: gutils.DockArea):
        super().__init__(parent)
        self.plugin = 'Qutag'
        self.setup_ui()
        self.acquiring = False

    def make_dock(self, name, title, viewer_type, next_to=None, which=None):
        self.docks[name] = Dock(title)
        if next_to is None:
            self.dockarea.addDock(self.docks[name])
        else:
            self.dockarea.addDock(self.docks[name], next_to, which)
        widget = QWidget()
        viewer = viewer_type(widget, show_toolbar=False)
        self.docks[name].addWidget(widget)
        return viewer

    def setup_docks(self):
        self.ch1_viewer = self.make_dock('ch1', 'Channel 1', Viewer1D)
        self.ch1_mean_viewer = \
            self.make_dock('ch1_mean', 'Mean 1', Viewer0D, "right",
                           self.docks['ch1'])
        self.ch1_sigma_viewer = \
            self.make_dock('ch1_sigma', 'Sigma 1', Viewer0D, "right",
                           self.docks['ch1_mean'])
        self.ch1_rate_viewer = \
            self.make_dock('ch1_rate', 'Rate 1', Viewer0D, "right",
                           self.docks['ch1_sigma'])

        self.ch2_viewer = \
            self.make_dock('ch2', 'Channel 2', Viewer1D, "bottom",
                           self.docks['ch1'])
        self.ch2_mean_viewer = \
            self.make_dock('ch2_mean', 'Mean 2', Viewer0D, "bottom",
                           self.docks['ch1_mean'])
        self.ch2_sigma_viewer = \
            self.make_dock('ch2_sigma', 'Sigma 2', Viewer0D, "bottom",
                           self.docks['ch1_sigma'])
        self.ch2_rate_viewer = \
            self.make_dock('ch2_rate', 'Rate 2', Viewer0D, "bottom",
                           self.docks['ch1_rate'])

        self.diff_viewer = \
            self.make_dock('diff', 'Difference', Viewer1D, "bottom",
                           self.docks['ch2'])
        self.diff_mean_viewer = \
            self.make_dock('diff_mean', 'Mean Diff.', Viewer0D, "bottom",
                           self.docks['ch2_mean'])
        self.diff_sigma_viewer = \
            self.make_dock('diff_sigma', 'Sigma Diff.', Viewer0D, "bottom",
                           self.docks['ch2_sigma'])
        self.docks['empty'] = Dock(name='')
        self.dockarea.addDock(self.docks['empty'], 'bottom',
                              self.docks['ch2_rate'])

        # separate window with raw detector data
        self.daq_viewer_area = DockArea()
        self.detector = \
            DAQ_Viewer(self.daq_viewer_area, title=self.plugin, init_h5=False)
        self.detector.daq_type = 'DAQ1D'
        self.detector.detector = self.plugin
        self.detector.init_hardware()

        self.mainwindow.set_shutdown_callback(self.detector.quit_fun)
        self.detector.grab_status.connect(self.mainwindow.disable_close)

    def setup_actions(self):
        self.add_action('acquire', 'Acquire', 'spectrumAnalyzer',
                        "Acquire", checkable=False, toolbar=self.toolbar)

    def connect_things(self):
        self.quit_action.triggered.connect(self.mainwindow.close)
        self.connect_action('acquire', self.start_acquiring)
        self.detector.grab_done_signal.connect(self.show_data)

    def setup_menu(self, menubar: QMenuBar = None):
        file_menu = self.mainwindow.menuBar().addMenu('File')
#        self.affect_to('save', file_menu)
#        file_menu.addSeparator()
        self.quit_action = file_menu.addAction("Quit", QKeySequence('Ctrl+Q'))

    def value_changed(self, param):
        pass

    def stop_acquiring(self):
        self.detector.stop()
        self.acquiring = False

    def start_acquiring(self):
        """Start acquisition"""

        if self.acquiring: # rather stop it
            self.stop_acquiring()
            return

        self.acquiring = True
        self.detector.grab()

    def get_mean_and_sigma(self, x, y):
        total = sum(y)
        mean = np.dot(x, y) / total
        sigma = np.sqrt(np.dot((x - mean)**2, y) / total)
        return mean, sigma

    def show_data(self, data: DataToExport):
        data1D = data.get_data_from_dim('Data1D')
        mean, sigma = \
            self.get_mean_and_sigma(data1D[0].axes[0].get_data(),
                                    data1D[0].data[0])
        self.ch1_viewer.show_data(data1D[0])
        self.ch1_mean_viewer.show_data(DataWithAxes(name="mean", dim='Data0D',
                                                    source='calculated',
                                                    data=[np.array([mean])]))
        self.ch1_sigma_viewer.show_data(DataWithAxes(name="sigma", dim='Data0D',
                                                     source='calculated',
                                                     data=[np.array([sigma])]))

        mean, sigma = \
            self.get_mean_and_sigma(data1D[1].axes[0].get_data(),
                                    data1D[1].data[0])
        self.ch2_viewer.show_data(data1D[1])
        self.ch2_mean_viewer.show_data(DataWithAxes(name="mean", dim='Data0D',
                                                    source='calculated',
                                                    data=[np.array([mean])]))
        self.ch2_sigma_viewer.show_data(DataWithAxes(name="sigma", dim='Data0D',
                                                     source='calculated',
                                                     data=[np.array([sigma])]))

        mean, sigma = \
            self.get_mean_and_sigma(data1D[2].axes[0].get_data(),
                                    data1D[2].data[0])
        self.diff_viewer.show_data(data1D[2])
        self.diff_mean_viewer.show_data(DataWithAxes(name="mean", dim='Data0D',
                                                     source='calculated',
                                                     data=[np.array([mean])]))
        self.diff_sigma_viewer.show_data(DataWithAxes(name="sigma", dim='Data0D',
                                                      source='calculated',
                                                      data=[np.array([sigma])]))


def main():
    from pymodaq_gui.utils.utils import mkQApp
    from qtpy.QtCore import pyqtRemoveInputHook
    app = mkQApp('CustomApp')
    pyqtRemoveInputHook() # needed for using pdb inside the qt eventloop

    mainwindow = MainWindow()
    dockarea = gutils.DockArea()
    mainwindow.setCentralWidget(dockarea)

    prog = QuTAGApp(dockarea)

    mainwindow.show()

    app.exec()


if __name__ == '__main__':
    main()
