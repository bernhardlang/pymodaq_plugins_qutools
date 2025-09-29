from qtpy import QtWidgets

from qtpy.QtWidgets import QMainWindow, QWidget, QApplication, QProgressBar, \
    QFileDialog # <<--
from pymodaq_gui import utils as gutils
from pymodaq_utils.config import Config
from pymodaq_utils.logger import set_logger, get_module_name
from pymodaq_gui.utils.dock import DockArea, Dock
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

    def setup_docks(self):
        self.docks['ch1'] = Dock('Channel 1')
        self.dockarea.addDock(self.docks['ch1'])
        self.ch1_widget = QWidget()
        self.ch1_viewer = Viewer1D(self.ch1_widget)
        self.docks['ch1'].addWidget(self.ch1_widget)

        self.docks['ch1_mean'] = Dock('Channel 1 Mean')
        self.dockarea.addDock(self.docks['ch1_mean'], "right", self.docks['ch1'])
        self.ch1_mean_widget = QWidget()
        self.ch1_mean_viewer = Viewer1D(self.ch1_mean_widget)
        self.docks['ch1_mean'].addWidget(self.ch1_mean_widget)

        self.docks['ch1_sigma'] = Dock('Channel 1 Sigma')
        self.dockarea.addDock(self.docks['ch1_sigma'], "right",
                              self.docks['ch1'])
        self.ch1_sigma_widget = QWidget()
        self.ch1_sigma_viewer = Viewer1D(self.ch1_sigma_widget)
        self.docks['ch1_sigma'].addWidget(self.ch1_sigma_widget)

        self.docks['ch2'] = Dock('Channel 2')
        self.dockarea.addDock(self.docks['ch2'], "bottom", self.docks['ch1'])
        self.ch2_widget = QWidget()
        self.ch2_viewer = Viewer1D(self.ch2_widget)
        self.docks['ch2'].addWidget(self.ch2_widget)

        self.docks['ch2_mean'] = Dock('Channel 2 Mean')
        self.dockarea.addDock(self.docks['ch2_mean'], "bottom",
                              self.docks['ch1_mean'])
        self.ch2_mean_widget = QWidget()
        self.ch2_mean_viewer = Viewer1D(self.ch2_mean_widget)
        self.docks['ch2_mean'].addWidget(self.ch2_mean_widget)

        self.docks['ch2_sigma'] = Dock('Channel 2 Sigma')
        self.dockarea.addDock(self.docks['ch2_sigma'], "bottom",
                              self.docks['ch1_sigma'])
        self.ch2_sigma_widget = QWidget()
        self.ch2_sigma_viewer = Viewer1D(self.ch2_sigma_widget)
        self.docks['ch2_sigma'].addWidget(self.ch2_sigma_widget)
        
        self.docks['ch3'] = Dock('Channel 3')
        self.dockarea.addDock(self.docks['ch3'], "bottom", self.docks['ch2'])
        self.ch3_widget = QWidget()
        self.ch3_viewer = Viewer1D(self.ch3_widget)
        self.docks['ch3'].addWidget(self.ch3_widget)

        self.docks['ch3_mean'] = Dock('Channel 3 Mean')
        self.dockarea.addDock(self.docks['ch3_mean'], "bottom",
                              self.docks['ch2_mean'])
        self.ch3_mean_widget = QWidget()
        self.ch3_mean_viewer = Viewer1D(self.ch3_mean_widget)
        self.docks['ch3_mean'].addWidget(self.ch3_mean_widget)

        self.docks['ch3_sigma'] = Dock('Channel 3 Sigma')
        self.dockarea.addDock(self.docks['ch3_sigma'], "bottom",
                              self.docks['ch2_sigma'])
        self.ch3_sigma_widget = QWidget()
        self.ch3_sigma_viewer = Viewer1D(self.ch3_sigma_widget)
        self.docks['ch3_sigma'].addWidget(self.ch3_sigma_widget)
        
    def setup_actions(self):
        pass

    def connect_things(self):
        pass

    def setup_menu(self, menubar: QtWidgets.QMenuBar = None):
        """Non mandatory method to be subclassed in order to create a menubar

        create menu for actions contained into the self._actions, for instance:

        Examples
        --------
        >>>file_menu = menubar.addMenu('File')
        >>>self.affect_to('load', file_menu)
        >>>self.affect_to('save', file_menu)

        >>>file_menu.addSeparator()
        >>>self.affect_to('quit', file_menu)

        See Also
        --------
        pymodaq.utils.managers.action_manager.ActionManager
        """
        # todo create and populate menu using actions defined above in self.setup_actions
        pass

    def value_changed(self, param):
        """ Actions to perform when one of the param's value in self.settings is changed from the
        user interface

        For instance:
        if param.name() == 'do_something':
            if param.value():
                print('Do something')
                self.settings.child('main_settings', 'something_done').setValue(False)

        Parameters
        ----------
        param: (Parameter) the parameter whose value just changed
        """
        pass


def main():
    from pymodaq_gui.utils.utils import mkQApp
    app = mkQApp('CustomApp')

    mainwindow = QtWidgets.QMainWindow()
    dockarea = gutils.DockArea()
    mainwindow.setCentralWidget(dockarea)

    prog = QuTAGApp(dockarea)

    mainwindow.show()

    app.exec()


if __name__ == '__main__':
    main()
