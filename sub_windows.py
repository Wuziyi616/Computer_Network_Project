import os

from PyQt5.QtGui import QPalette, QBrush, QPixmap
from PyQt5.QtWidgets import QWidget, QAbstractItemView

from UI.log_in_window import Ui_Form as LogInWindow
from UI.add_group_window import Ui_Form as AddGroupWindow

import config


class LogInWin(QWidget, LogInWindow):

    def __init__(self, parent=None):
        super(LogInWin, self).__init__(parent)
        self.setupUi(self)

        # background image
        palette = QPalette()
        palette.setBrush(self.backgroundRole(), QBrush(QPixmap(config.LOG_IN_WINDOW_BG)))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.log_inBtn.setFlat(True)

    def closeEvent(self, event):
        """Kill all the threads."""
        os._exit(0)


class AddGroupWin(QWidget, AddGroupWindow):

    def __init__(self, parent=None):
        super(AddGroupWin, self).__init__(parent)
        self.setupUi(self)

        self.all_userLW.setSelectionMode(QAbstractItemView.MultiSelection)
