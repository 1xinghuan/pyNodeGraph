# -*- coding: utf-8 -*-

import os
from pyNodeGraph.module.sqt import *
from pyNodeGraph.ui.graph.view import GraphicsSceneWidget
from pyNodeGraph.ui.parameter.param_panel import ParameterPanel
from pyNodeGraph.core.state.core import GraphState
from pyNodeGraph.core.node.node import Node
from pyNodeGraph.utils.settings import User_Setting, read_setting, write_setting
from pyNodeGraph.utils.res import resource
from pyNodeGraph.ui.utils.menu import WithMenuObject
from pyNodeGraph.core.plugin.setup import *


PY_NODE_GRAPH_WINDOW = None


class DockWidget(QtWidgets.QDockWidget):
    maximizedRequired = QtCore.Signal()

    def __init__(self, title='', objName='', *args, **kwargs):
        super(DockWidget, self).__init__(*args, **kwargs)

        self.setObjectName(objName)
        self.setWindowTitle(title)

    def keyPressEvent(self, event):
        super(DockWidget, self).keyPressEvent(event)

        if event.key() == QtCore.Qt.Key_Space:
            self.maximizedRequired.emit()


class NodeGraphTab(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super(NodeGraphTab, self).__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.setMovable(True)


class PyNodeGraph(QtWidgets.QMainWindow, WithMenuObject):
    entityItemDoubleClicked = QtCore.Signal(object)
    currentSceneChanged = QtCore.Signal(object)
    mainWindowClosed = QtCore.Signal()

    _addedActions = []
    _addedWidgetClasses = []

    @classmethod
    def registerActions(cls, actionList):
        cls._addedActions = actionList

    @classmethod
    def registerDockWidget(cls, widgetClass, name, label):
        cls._addedWidgetClasses.append([
            widgetClass, name, label
        ])

    @classmethod
    def getInstance(cls):
        return PY_NODE_GRAPH_WINDOW

    def __init__(
            self, app='main',
            parent=None
    ):
        super(PyNodeGraph, self).__init__(parent=parent)

        global PY_NODE_GRAPH_WINDOW
        PY_NODE_GRAPH_WINDOW = self

        self.app = app

        self.currentScene = None
        self._file = None
        self.scenes = []
        self._docks = []
        self._maxDock = None

        self._initUI()
        self._createSignal()

    def _createSignal(self):
        self.applyButton.clicked.connect(self._applyActionTriggered)
        self.nodeGraphTab.tabCloseRequested.connect(self._tabCloseRequest)
        self.nodeGraphTab.currentChanged.connect(self._tabChanged)

        for dock in self._docks:
            dock.maximizedRequired.connect(self._dockMaxRequired)

    def _getNodeActions(self):
        actions = []
        groupDict = Node.getNodesByGroup()
        groups = list(groupDict.keys())
        groups.sort()
        for group in groups:
            nodeActions = []
            nodes = groupDict[group]
            for node in nodes:
                nodeActions.append([node.nodeType, node.nodeType, None, self._nodeActionTriggered])
            actions.append([group, nodeActions])

        return [['Node', actions]]

    def _getMenuActions(self):
        actions = [
            ['File', [
                ['new_file', 'New', 'Ctrl+N', self._newActionTriggered],
                ['open_file', 'Open', 'Ctrl+O', self._openActionTriggered],
                ['save_nodes', 'Save', 'Ctrl+S', self._saveNodesActionTriggered],
                ['execute', 'Execute', 'Ctrl+E', self._applyActionTriggered],
                ['separater'],
                ['import_nodes', 'Import Nodes', None, self._importNodesActionTriggered],
                ['export_nodes', 'Export Nodes', None, self._exportNodesActionTriggered],

            ]],
            ['Edit', [
                ['create_node', 'Create Node', 'Tab', self._createNodeActionTriggered],
                ['select_all_node', 'Select All', 'Ctrl+A', self._selectAllActionTriggered],
                ['copy_node', 'Copy', 'Ctrl+C', self._copyActionTriggered],
                ['cut_node', 'Cut', 'Ctrl+X', self._cutActionTriggered],
                ['paste_node', 'Paste', 'Ctrl+V', self._pasteActionTriggered],
                ['delete_selection', 'Delete Selection', 'Del', self._deleteSelectionActionTriggered],
                ['separater'],
                # ['disable_selection', 'Disable Selection', 'D', self._disableSelectionActionTriggered],
                # ['enter_node', 'Enter', 'Ctrl+Return', self._enterActionTriggered],
            ]],
            ['View', [
                ['frame_selection', 'Frame Selection', None, self._frameSelectionActionTriggered],
            ]]
        ]
        actions.extend(self._getNodeActions())
        actions.extend(self._addedActions)
        return actions

    def _setMenus(self):
        self._addSubMenus(self.menuBar(), self._getMenuActions())

    def _initUI(self):
        self.setWindowTitle('Py Node Graph')
        self.setDockNestingEnabled(True)
        self.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)

        self._geometry = None
        self._state = None

        self._setMenus()

        self.nodeGraphTab = NodeGraphTab(parent=self)
        self.buttonsWidget = QtWidgets.QWidget(parent=self)
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.setAlignment(QtCore.Qt.AlignRight)
        buttonLayout.setContentsMargins(0, 0, 10, 0)
        self.buttonsWidget.setLayout(buttonLayout)
        self.nodeGraphTab.setCornerWidget(self.buttonsWidget, QtCore.Qt.TopRightCorner)

        self.applyButton = QtWidgets.QPushButton()
        self.applyButton.setIcon(resource.get_qicon('btn', 'run.png'))
        buttonLayout.addWidget(self.applyButton)

        self.parameterPanel = ParameterPanel(parent=self)

        self._addNewScene()

        self.nodeGraphDock = DockWidget(title='Node Graph', objName='nodeGraphDock')
        self.nodeGraphDock.setWidget(self.nodeGraphTab)
        self.parameterPanelDock = DockWidget(title='Parameters', objName='parameterPanelDock')
        self.parameterPanelDock.setWidget(self.parameterPanel)

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.nodeGraphDock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.parameterPanelDock)

        self._docks.append(self.nodeGraphDock)
        self._docks.append(self.parameterPanelDock)

        for widgetClass, name, label in self._addedWidgetClasses:
            dock = DockWidget(title=label, objName=name)
            widget = widgetClass()
            dock.setWidget(widget)

            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
            self._docks.append(dock)

        # self._getUiPref()

    def _dockMaxRequired(self):
        dockWidget = self.sender()
        if dockWidget == self._maxDock:
            # for w in self._docks:
            #     w.setVisible(True)
            self._maxDock = None

            self.restoreState(self._state)
        else:
            self._state = self.saveState()

            for w in self._docks:
                w.setVisible(w == dockWidget)
            self._maxDock = dockWidget

    def _switchScene(self):
        self.currentScene = self.nodeGraphTab.currentWidget()
        if self.currentScene is not None:
            self.currentSceneChanged.emit(self.currentScene.scene)

    def _addFile(self, path):
        self._addScene(path)

    def _addNewScene(self, path=None):
        newScene = GraphicsSceneWidget(
            parent=self
        )
        if path is not None:
            newScene.setFile(path, reset=False)

        self.scenes.append(newScene)
        self.nodeGraphTab.addTab(newScene, 'Scene')

        newScene.itemDoubleClicked.connect(self._itemDoubleClicked)
        newScene.enterFileRequired.connect(self._enterFileRequired)
        newScene.scene.nodeDeleted.connect(self._nodeDeleted)

        self.nodeGraphTab.setCurrentWidget(newScene)
        self._switchScene()

        GraphState.executeCallbacks(
            'sceneAdded', path=path
        )

        return newScene

    def _addScene(self, path):
        newScene = None
        for scene in self.scenes:
            if scene.path == path:
                self.nodeGraphTab.setCurrentWidget(scene)
                return

        if newScene is None:
            newScene = self._addNewScene(path)
            newScene.scene.resetScene()

        self.nodeGraphTab.setTabText(len(self.scenes) - 1, os.path.basename(path))
        self.nodeGraphTab.setTabToolTip(len(self.scenes) - 1, path)

        # self._switchScene()

    def _tabCloseRequest(self, index):
        if self.nodeGraphTab.count() > 0:
            scene = self.nodeGraphTab.widget(index)
            self.nodeGraphTab.removeTab(index)
            self.scenes.remove(scene)

    def _tabChanged(self, index):
        self._switchScene()

    def _itemDoubleClicked(self, item):
        self.parameterPanel.addNode(item)
        self.entityItemDoubleClicked.emit(item)

    def _enterFileRequired(self, path):
        path = str(path)
        self._addFile(path)

    def _nodeDeleted(self, node):
        self.parameterPanel.removeNode(node.name())

    def _nodeActionTriggered(self):
        nodeType = self.sender().objectName()
        self.currentScene.scene.createNode(nodeType)

    def _newActionTriggered(self):
        self._addNewScene()

    def _openActionTriggered(self):
        file = QtWidgets.QFileDialog.getOpenFileName(None, 'Select File', filter='PY Node Graph(*.pyng *.xml)')
        if isinstance(file, tuple):
            file = file[0]
        file = str(file)
        if os.path.exists(file):
            # self.setFile(file)
            self._addFile(file)

    def _importNodesActionTriggered(self):
        xmlFile = QtWidgets.QFileDialog.getOpenFileName(None, 'Import File', filter='PY Node Graph(*.pyng *.xml)')
        if isinstance(xmlFile, tuple):
            xmlFile = xmlFile[0]
        xmlFile = str(xmlFile)
        if os.path.exists(xmlFile):
            with open(xmlFile, 'r') as f:
                nodesString = f.read()
            nodes = self.currentScene.scene.pasteNodesFromXml(nodesString)

    def _exportNodesActionTriggered(self):
        xmlFile = QtWidgets.QFileDialog.getSaveFileName(None, 'Export', filter='PY Node Graph(*.pyng *.xml)')
        if isinstance(xmlFile, tuple):
            xmlFile = xmlFile[0]
        xmlFile = str(xmlFile)
        if xmlFile == '':
            return
        if not xmlFile.endswith('.pyng'):
            xmlFile += '.pyng'
        self.currentScene.scene.exportSelectedNodesToFile(xmlFile)

    def _saveNodesActionTriggered(self):
        self.currentScene.saveNodes()

    def _applyActionTriggered(self):
        self.currentScene.execute()

    def _createNodeActionTriggered(self):
        self.currentScene.view.showFloatEdit()

    def _selectAllActionTriggered(self):
        self.currentScene.scene.selectAll()

    def _copyActionTriggered(self):
        nodesString = self.currentScene.scene.getSelectedNodesAsXml()
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(nodesString)

    def _pasteActionTriggered(self):
        nodesString = str(QtWidgets.QApplication.clipboard().text())
        nodes = self.currentScene.scene.pasteNodesFromXml(nodesString)

    def _cutActionTriggered(self):
        self._copyActionTriggered()
        self._deleteSelectionActionTriggered()

    def _enterActionTriggered(self):
        self.currentScene.scene.enterSelection()

    def _frameSelectionActionTriggered(self):
        self.currentScene.scene.frameSelection()

    def _layoutActionTriggered(self):
        self.currentScene.scene.layoutNodes()

    def _disableSelectionActionTriggered(self):
        self.currentScene.scene.disableSelection()

    def _deleteSelectionActionTriggered(self):
        self.currentScene.scene.deleteSelection()

    def _clearScenes(self):
        for i in range(self.nodeGraphTab.count()):
            self._tabCloseRequest(i)

    def setFile(self, file):
        self._file = file
        self._clearScenes()
        self._addFile(file)

    def addFile(self, file):
        self._addFile(file)

    def createNode(self, nodeType):
        node = self.currentScene.scene.createNode(nodeType)
        return node

    def closeEvent(self, event):
        super(PyNodeGraph, self).closeEvent(event)
        self.mainWindowClosed.emit()

    def showEvent(self, QShowEvent):
        super(PyNodeGraph, self).showEvent(QShowEvent)
        self._getUiPref()

    def hideEvent(self, QHideEvent):
        write_setting(User_Setting, 'nodegraph_geo/{}'.format(self.app), value=self.saveGeometry())
        write_setting(User_Setting, 'nodegraph_state/{}'.format(self.app), value=self.saveState())
        super(PyNodeGraph, self).hideEvent(QHideEvent)

    def _getUiPref(self):
        geo = read_setting(
            User_Setting,
            'nodegraph_geo/{}'.format(self.app),
            to_type='bytearray')
        state = read_setting(
            User_Setting,
            'nodegraph_state/{}'.format(self.app),
            to_type='bytearray')

        self.restoreGeometry(geo)
        self.restoreState(state)

