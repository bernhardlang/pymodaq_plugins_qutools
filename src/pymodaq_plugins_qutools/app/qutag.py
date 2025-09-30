from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QMainWindow, QWidget, QApplication, QProgressBar, \
    QFileDialog, QMenuBar # <<--
from pymodaq_gui import utils as gutils
from pymodaq_utils.config import Config
from pymodaq_utils.logger import set_logger, get_module_name
from pymodaq_gui.utils.dock import DockArea, Dock
from pymodaq_gui.utils.main_window import MainWindow
from pymodaq_gui.plotting.data_viewers.viewer1D import Viewer1D
from pymodaq_plugins_qutools.utils import Config as PluginConfig

logger = set_logger(get_module_name(__file__))

main_config = Config()
plugin_config = PluginConfig()


class QuTAGApp(gutils.CustomApp):

    params = []

    def __init__(self, parent: gutils.DockArea):
        super().__init__(parent)
        self.setup_ui()
        self.acquiring = False

    def make_dock(self, name, title, next_to=None, which=None):
        self.docks[name] = Dock(title)
        if next_to is None:
            self.dockarea.addDock(self.docks[name])
        else:
            self.dockarea.addDock(self.docks[name], next_to, which)
        widget = QWidget()
        viewer = Viewer1D(widget, show_toolbar=False)
        self.docks[name].addWidget(widget)
        return viewer
        
    def setup_docks(self):
        self.ch1_viewer = self.make_dock('ch1', 'Channel 1')
        self.ch1_mean_viewer = \
            self.make_dock('ch1_mean', 'Mean 1', "right", self.docks['ch1'])
        self.ch1_sigma_viewer = \
            self.make_dock('ch1_sigma', 'Sigma 1', "right",
                           self.docks['ch1_mean'])
        self.ch1_rate_viewer = \
            self.make_dock('ch1_rate', 'Rate 1', "right",
                           self.docks['ch1_sigma'])

        self.ch2_viewer = \
            self.make_dock('ch2', 'Channel 2', "bottom", self.docks['ch1'])
        self.ch2_mean_viewer = \
            self.make_dock('ch2_mean', 'Mean 2', "bottom",
                           self.docks['ch1_mean'])
        self.ch2_sigma_viewer = \
            self.make_dock('ch2_sigma', 'Sigma 2', "bottom",
                           self.docks['ch1_sigma'])
        self.ch2_rate_viewer = \
            self.make_dock('ch2_rate', 'Rate 2', "bottom",
                           self.docks['ch1_rate'])

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
        pass

    def start_acquiring(self):
        """Start acquisition"""

        if self.acquiring: # rather stop it
            self.stop_acquiring()
            return

        self.acquiring = True


def main():
    from pymodaq_gui.utils.utils import mkQApp
    app = mkQApp('CustomApp')

    mainwindow = MainWindow()
    dockarea = gutils.DockArea()
    mainwindow.setCentralWidget(dockarea)

    prog = QuTAGApp(dockarea)

    mainwindow.show()

    app.exec()


if __name__ == '__main__':
    main()
