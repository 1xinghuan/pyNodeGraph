# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 5/10/2019

from pyNodeGraph.module.sqt import *
import weakref


RED_COLOR = QtGui.QColor(221, 30, 30)


class ScriptStdout:
    def __init__(self, outputWindow):
        self._outputWindowRef = weakref.ref(outputWindow)
        self.stdoutTextFormat = QtGui.QTextCharFormat()
        self.defaultTextColor = outputWindow.palette().color(outputWindow.foregroundRole())
        self.stdoutTextFormat.setForeground(self.defaultTextColor)

    def write(self, text):
        outputWindow = self._outputWindowRef()
        if not outputWindow:
            return
        if text.startswith('DEBUG'):
            self.stdoutTextFormat.setForeground(QtGui.QColor(85, 170, 85))
        elif text.startswith('INFO'):
            self.stdoutTextFormat.setForeground(QtGui.QColor(119, 221, 119))
        elif text.startswith('WARNING'):
            self.stdoutTextFormat.setForeground(RED_COLOR)
        elif text.startswith('ERROR'):
            self.stdoutTextFormat.setForeground(RED_COLOR)
        else:
            self.stdoutTextFormat.setForeground(self.defaultTextColor)
        outputWindow.moveCursor(QtGui.QTextCursor.End)
        outputWindow.textCursor().insertText(text, self.stdoutTextFormat)

    def flush(self):
        pass


class ScriptStderr:
    def __init__(self, outputWindow, realstderr):
        self._outputWindowRef = weakref.ref(outputWindow)
        self.errorTextFormat = QtGui.QTextCharFormat()
        self.errorTextFormat.setFontWeight(QtGui.QFont.Normal)
        self.errorTextFormat.setForeground(RED_COLOR)

        self.pop = False

    def write(self, text):
        outputWindow = self._outputWindowRef()
        if not outputWindow:
            return
        outputWindow.moveCursor(QtGui.QTextCursor.End)
        outputWindow.textCursor().insertText(text, self.errorTextFormat)
        outputWindow.textCursor().movePosition(QtGui.QTextCursor.End)

        if self.pop:
            logWindow = outputWindow.parent()
            if not logWindow.isActiveWindow():
                logWindow.showMinimized()
                logWindow.showNormal()
                logWindow.activateWindow()

    def flush(self):
        pass


class ScriptStdin:
    def __init__(self, window):
        pass


