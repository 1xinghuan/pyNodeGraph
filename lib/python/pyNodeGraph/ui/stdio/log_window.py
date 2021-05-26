# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 11/6/2018

import time
import sys
import logging
from pyNodeGraph.module.sqt import *
from pyNodeGraph.utils.log import set_logger
from .io_stream import ScriptStderr, ScriptStdout, ScriptStdin


class LogWindow(QtWidgets.QWidget):
    def __init__(self):
        super(LogWindow, self).__init__()

        self.init_ui()
        self.redirect_output()

    def init_ui(self):
        self.setWindowTitle('PyNodeGraph Log Window')

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.masterLayout)

        self._outputWindow = QtWidgets.QTextEdit(parent=self)
        self._outputWindow.setStyleSheet("""
                        background: palette(window)
                        """)
        self._outputWindow.setReadOnly(True)
        self._outputWindow.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        self.masterLayout.addWidget(self._outputWindow)

        self.setGeometry(200, 200, 500, 300)

    def redirect_output(self):
        self.stdout = ScriptStdout(self._outputWindow)
        self.stderr = ScriptStderr(self._outputWindow, sys.stdout)
        # self.stderr.pop = True
        self.stdin = ScriptStdin(self)

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdin = sys.stdin
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        sys.stdin = self.stdin

        root_logger = logging.getLogger()
        set_logger(root_logger)
        # root_logger.removeHandler(root_logger.handlers[1])
        root_logger.handlers[0].stream = sys.stdout
        # root_logger.handlers[1].stream = sys.stdout


def get_log_window():
    log_window = LogWindow()
    log_window.show()
    return log_window
