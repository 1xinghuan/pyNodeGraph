# -*- coding: utf-8 -*-

import os
import re
import json
import time
from pyNodeGraph.module.sqt import *
from pyNodeGraph.utils.const import VIEWPORT_FULL_UPDATE
from pyNodeGraph.core.node import Node
from pyNodeGraph.utils.log import get_logger, log_cost_time
from pyNodeGraph.core.state import GraphState
from pyNodeGraph.core.parse._xml import ET, convertToString
from pyNodeGraph.utils.res import resource
from pyNodeGraph.ui.utils.menu import WithMenuObject
from pyNodeGraph.ui.utils.drop import DropWidget
from .nodeItem import NodeItem
from .other.pipe import Pipe
from .other.port import Port


logger = get_logger('pyNodeGraph.view')


NODE_NAME_PATTERN = re.compile('(?P<suffix>[^\d]*)(?P<index>\d+)')
VARIANT_PRIM_PATH_PATTERN = re.compile('.*{(?P<variantSet>.+)=(?P<variant>.+)}$')

VIEW_FILL_COLOR = QtGui.QColor(38, 38, 38)
VIEW_LINE_COLOR = QtGui.QColor(55, 55, 55)
DISABLE_LINE_COLOR = QtGui.QColor(95, 75, 75)
VIEW_CENTER_LINE_COLOR = QtGui.QColor(80, 80, 60, 50)
VIEW_GRID_WIDTH = 200
VIEW_GRID_HEIGHT = 100

VIEW_ZOOM_STEP = 1.1


class FloatLineEdit(QtWidgets.QFrame):
    editFinished = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(FloatLineEdit, self).__init__(*args, **kwargs)

        self.masterLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.masterLayout)

        self._edit = QtWidgets.QLineEdit()
        self.masterLayout.addWidget(self._edit)

        self.setFixedWidth(200)
        self.setStyleSheet('QFrame{border-radius: 5px}')

        self._edit.editingFinished.connect(self._editFinished)
        self._edit.returnPressed.connect(self._returnPressed)

    def _editFinished(self):
        # self.editFinished.emit(self._edit.text())
        self.setVisible(False)

    def _returnPressed(self):
        self.editFinished.emit(self._edit.text())
        self.setVisible(False)
        self.parent().setFocus()
        self._edit.setFocus()

    def reset(self):
        allNodeClass = Node.getAllNodeClassNames()
        completer = QtWidgets.QCompleter(allNodeClass)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._edit.setCompleter(completer)
        self._edit.setText('')

    def setVisible(self, bool):
        super(FloatLineEdit, self).setVisible(bool)
        if bool:
            self._edit.setFocus()


class GraphicsView(QtWidgets.QGraphicsView, DropWidget, WithMenuObject):
    def __init__(self, *args, **kwargs):
        super(GraphicsView, self).__init__(*args, **kwargs)
        DropWidget.__init__(self)

        self.setAcceptExts([])
        # self.addDropLabel()

        self.currentZoom = 1.0
        self.panningMult = 2.0 * self.currentZoom
        self.panning = False
        self.keyZooming = False
        self.clickedPos = QtCore.QPoint(0, 0)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        if VIEWPORT_FULL_UPDATE == '0':
            self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        else:
            self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        # self.setRenderHint(QtGui.QPainter.Antialiasing)

        self._createNewFloatEdit = FloatLineEdit(self)
        self._createNewFloatEdit.setVisible(False)

        self._createNewFloatEdit.editFinished.connect(self._floatEditFinished)

    def dragEnterEvent(self, QDragEnterEvent):
        DropWidget.dragEnterEvent(self, QDragEnterEvent)

    def dragLeaveEvent(self, QDragLeaveEvent):
        DropWidget.dragLeaveEvent(self, QDragLeaveEvent)

    def dragMoveEvent(self, QDragMoveEvent):
        DropWidget.dragMoveEvent(self, QDragMoveEvent)

    def dropEvent(self, QDropEvent):
        DropWidget.dropEvent(self, QDropEvent)

    def afterFilesDrop(self, acceptFiles):
        pass

    def _zoom(self, zoom):
        self.scale(zoom, zoom)
        self.currentZoom = self.transform().m11()
        self._resizeScene()

    def getCenterPos(self):
        center = self.mapToScene(QtCore.QPoint(
            self.viewport().width() / 2,
            self.viewport().height() / 2
        ))
        return center

    def _resizeScene(self, setLabel=True):
        center = self.getCenterPos()
        w = self.viewport().width() / self.currentZoom * 2 + 25000
        h = self.viewport().height() / self.currentZoom * 2 + 25000

        self.scene().setSceneRect(QtCore.QRectF(
            center.x() - w / 2,
            center.y() - h / 2,
            w,
            h
        ))

        self._setAntialiasing()

        if setLabel:
            self._setLabelVisible()

    def _setAntialiasing(self):
        antialiasing = True if self.currentZoom >= 0.1 else False
        self.setRenderHint(QtGui.QPainter.Antialiasing, antialiasing)

    def _setLabelVisible(self):
        showPortLabel = True if self.currentZoom >= 1 else False
        showNodeLabel = True if self.currentZoom >= 0.5 else False

        point1 = self.mapToScene(QtCore.QPoint(-20, -20))
        point2 = self.mapToScene(QtCore.QPoint(self.viewport().width(), self.viewport().height()))
        rect = QtCore.QRectF(point1, point2)

        for node in self.scene().allNodes():
            node.setLabelVisible(showNodeLabel and rect.contains(node.pos()))
            for port in node.ports:
                port.setLabelVisible(showPortLabel and rect.contains(port.scenePos()))

    def focusNextPrevChild(self, bool):
        return False

    def keyReleaseEvent(self, event):
        super(GraphicsView, self).keyReleaseEvent(event)
        if not self._createNewFloatEdit.isVisible():
            if event.key() == QtCore.Qt.Key_F:
                self.scene().frameSelection()

    def fitTo(self, items=[]):
        if len(items) == 0:
            for item in self.scene().items():
                if isinstance(item, NodeItem):
                    items.append(item)

        max_x = items[0].pos().x()
        min_x = items[0].pos().x()
        max_y = items[0].pos().y()
        min_y = items[0].pos().y()
        for item in items:
            max_x = max(item.pos().x(), max_x)
            min_x = min(item.pos().x(), min_x)
            max_y = max(item.pos().y(), max_y)
            min_y = min(item.pos().y(), min_y)
        center_x = (max_x + min_x) / 2 + 100
        center_y = (max_y + min_y) / 2 + 40
        width = max_x - min_x
        height = max_y - min_y

        zoom_x = 1 / max(1, float(width + 1000) / self.viewport().width()) / self.currentZoom
        zoom_y = 1 / max(1, float(height + 1000) / self.viewport().height()) / self.currentZoom
        zoom = min(zoom_x, zoom_y)
        self.scale(zoom, zoom)
        self.currentZoom = self.transform().m11()
        self._resizeScene()

        self.centerOn(QtCore.QPointF(center_x, center_y))

    def mousePressEvent(self, event):
        """Initiate custom panning using middle mouse button."""
        selectedItems = self.scene().selectedItems()
        self.clickedPos = event.pos()

        if self.panning:
            if event.button() == QtCore.Qt.RightButton:
                self.keyZooming = True
                self.panning = False
                self.setCursor(QtCore.Qt.ArrowCursor)
                return

        if event.button() == QtCore.Qt.MiddleButton:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.panning = True
            self.prevPos = event.pos()
            self.prevCenter = self.getCenterPos()
            self.setCursor(QtCore.Qt.SizeAllCursor)
        elif event.button() == QtCore.Qt.LeftButton:
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        super(GraphicsView, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.MiddleButton:
            for item in selectedItems:
                item.setSelected(True)
        self._highlightConnection()

    def mouseMoveEvent(self, event):
        if self.keyZooming:
            mouseMove = event.pos() - self.prevPos
            mouseMoveY = mouseMove.y()
            if mouseMoveY > 0: #  zoom in
                zoom = mouseMoveY * 0.01 + 1
                self._zoom(zoom)
            elif mouseMoveY < 0:
                zoom = 1.0 / (-mouseMoveY * 0.01 + 1)
                self._zoom(zoom)

            self.prevPos = event.pos()
        if self.panning:
            mouseMove = event.pos() - self.prevPos
            newCenter = QtCore.QPointF(
                self.prevCenter.x() - mouseMove.x() / self.currentZoom,
                self.prevCenter.y() - mouseMove.y() / self.currentZoom
            )
            self.centerOn(newCenter)
            self._resizeScene(setLabel=False)
            return
        super(GraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)
        if self.keyZooming:
            self.keyZooming = False

        super(GraphicsView, self).mouseReleaseEvent(event)

        self._highlightConnection()
        self.clickedPos = event.pos()
        self._resizeScene()

    def wheelEvent(self, event):
        positive = event.delta() >= 0
        zoom = VIEW_ZOOM_STEP if positive else 1.0 / VIEW_ZOOM_STEP
        self._zoom(zoom)

    def drawDisableLines(self, painter, rect):
        pen = QtGui.QPen(DISABLE_LINE_COLOR)
        pen.setCosmetic(True)
        pen.setWidth(1)
        painter.setPen(pen)

        lines = []
        lw = 50

        w = self.viewport().width()
        h = self.viewport().height()

        for i in range(int(w / lw)):
            point1 = self.mapToScene(QtCore.QPoint(i * lw, 0))
            point2 = self.mapToScene(QtCore.QPoint(0, i * lw))

            lines.append(QtCore.QLineF(point1, point2))

        for i in range(int(h / lw)):
            point1 = self.mapToScene(QtCore.QPoint(w, i * lw))
            point2 = self.mapToScene(QtCore.QPoint(w - (h - i * lw), h))

            lines.append(QtCore.QLineF(point1, point2))

        painter.drawLines(lines)

    def drawBackground(self, painter, rect):
        pen = QtGui.QPen(VIEW_LINE_COLOR)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(VIEW_FILL_COLOR))

        painter.drawRect(rect)
        lines = []
        scale = max(int(1 / self.currentZoom / 2), 1)
        line_w = VIEW_GRID_WIDTH * scale
        line_h = VIEW_GRID_HEIGHT * scale

        point1 = self.mapToScene(QtCore.QPoint(0, 0))
        point2 = self.mapToScene(QtCore.QPoint(self.viewport().width(), self.viewport().height()))

        for i in range(int(point1.y() / line_h), int(point2.y() / line_h) + 1):
            lines.append(QtCore.QLineF(
                QtCore.QPoint(rect.x(), i * line_h),
                QtCore.QPoint(rect.x() + rect.width(), i * line_h)
            ))

        for i in range(int(point1.x() / line_w), int(point2.x() / line_w) + 1):
            lines.append(QtCore.QLineF(
                QtCore.QPoint(i * line_w, rect.y()),
                QtCore.QPoint(i * line_w, rect.y() + rect.height())
            ))
        painter.drawLines(lines)

        painter.setPen(QtGui.QPen(VIEW_CENTER_LINE_COLOR))
        painter.drawLine(QtCore.QLineF(QtCore.QPoint(rect.x(), 0), QtCore.QPoint(rect.x() + rect.width(), 0)))
        painter.drawLine(QtCore.QLineF(QtCore.QPoint(0, rect.y()), QtCore.QPoint(0, rect.y() + rect.height())))

    def _highlightConnection(self):
        for item in self.scene().items():
            if isinstance(item, Port):
                for pipe in item.pipes:
                    pipe.setLineColor(highlight=False)
            # if isinstance(item, NodeItem):
            #     item.setHighlight(False)
        for item in self.scene().selectedItems():
            if isinstance(item, NodeItem):
                for port in item.ports:
                    for pipe in port.pipes:
                        pipe.setLineColor(highlight=True)

    def showFloatEdit(self):
        self._createNewFloatEdit.move(self.clickedPos)
        self._createNewFloatEdit.reset()
        self._createNewFloatEdit.setVisible(True)

    def _floatEditFinished(self, text):
        text = str(text)
        scenePos = self.mapToScene(self.clickedPos)
        node = self.scene().createNode(text, pos=[scenePos.x(), scenePos.y()])

    def _getContextMenus(self):
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

        return actions

    def _createContextMenu(self):
        self.menu = QtWidgets.QMenu(self)
        menus = []
        scenePos = self.mapToScene(self.clickedPos)
        item = self.scene().itemAt(scenePos, QtGui.QTransform())
        if item is None:
            menus = self._getContextMenus()
        elif isinstance(item, NodeItem):
            menus = item.getContextMenus()
        elif isinstance(item, Port):
            menus = item.getContextMenus()
        elif isinstance(item.parentItem(), NodeItem):
            menus = item.parentItem().getContextMenus()
        self._addSubMenus(self.menu, menus)

    def contextMenuEvent(self, event):
        super(GraphicsView, self).contextMenuEvent(event)
        if self.keyZooming:
            return
        self._createContextMenu()
        self.menu.move(QtGui.QCursor().pos())
        self.menu.show()

    def _nodeActionTriggered(self):
        nodeType = self.sender().objectName()
        scenePos = self.mapToScene(self.clickedPos)
        self.scene().createNode(nodeType, pos=[scenePos.x(), scenePos.y()])


class GraphicsSceneWidget(QtWidgets.QWidget):
    itemDoubleClicked = QtCore.Signal(object)
    showWidgetSignal = QtCore.Signal(int)
    enterFileRequired = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(GraphicsSceneWidget, self).__init__(parent=parent)

        self.path = None

        self._initUI()

        self.scene.enterFileRequired.connect(self._enterFileRequired)

    def _initUI(self):
        self.view = GraphicsView()
        self.scene = GraphicsScene(view=self.view, parent=self)
        self.view.setScene(self.scene)
        self.setGeometry(100, 100, 800, 600)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.scene.setSceneRect(QtCore.QRectF(
            -(self.view.viewport().width() / self.view.currentZoom * 2 + 25000) / 2,
            -(self.view.viewport().height() / self.view.currentZoom * 2 + 25000) / 2,
            self.view.viewport().width() / self.view.currentZoom * 2 + 25000,
            self.view.viewport().height() / self.view.currentZoom * 2 + 25000
        ))

    def setFile(self, path, reset=True):
        self.scene.setFile(path, reset=reset)

    def _getAbsPath(self, path):
        path = str(path)
        absPath = path
        return absPath

    def _enterFileRequired(self, filePath):
        absPath = self._getAbsPath(filePath)
        self.enterFileRequired.emit(absPath)

    def exportToString(self):
        return self.scene.exportToString()

    def exportToFile(self):
        self.scene.exportToFile()

    def saveLayer(self):
        self.scene.saveLayer()

    def saveNodes(self):
        self.scene.saveNodes()

    def execute(self):
        self.scene.execute()


class GraphicsScene(QtWidgets.QGraphicsScene):
    enterFileRequired = QtCore.Signal(str)
    nodeParameterChanged = QtCore.Signal(object)
    nodeDeleted = QtCore.Signal(object)

    def __init__(self, view=None, **kwargs):
        super(GraphicsScene, self).__init__(**kwargs)

        self.view = view

        self.path = None

        self._allNodes = {}
        self._nodesSuffix = {}
        self._primNodes = {}

        self.setSceneRect(QtCore.QRectF(-25000 / 2, -25000 / 2, 25000, 25000))

    def _addChildNode(self, node, upNode, index=0):
        if upNode is not None:
            node.setX(upNode.pos().x() + index * (upNode.w + 50))
            node.setY(upNode.pos().y() + upNode.h + 100)
            node.connectToNode(upNode)

    def getRootNode(self):
        nodes = self.getNodes(type='Main')
        if len(nodes) == 0:
            return
        return nodes[0]

    def _afterNodeNameChanged(self, node):
        self._allNodes[node] = node.name()

    def _getUniqueName(self, name):
        # nodes = self.allNodes()
        # names = [n.name() for n in nodes]
        names = list(self._allNodes.values())

        match = re.match(NODE_NAME_PATTERN, name)
        if match:
            suffix = match.group('suffix')
            index = int(match.group('index'))
        else:
            suffix = name
            index = 0

        if name not in names:
            return name, suffix, index

        if suffix in self._nodesSuffix:
            indexs = self._nodesSuffix.get(suffix)
            indexs.sort(reverse=True)
        else:
            indexs = []

        if len(indexs) > 0:
            index = indexs[0]

        while name in names:
            index += 1
            name = '{}{}'.format(suffix, index)

        return name, suffix, index

    def _executeNode(self, node):
        return

    def clear(self):
        for node in self.allNodes():
            self.deleteNode(node)
        super(GraphicsScene, self).clear()

    def _loadSceneFromUng(self, ungFile):
        with open(ungFile, 'r') as f:
            xmlString = f.read()
        self.pasteNodesFromXml(xmlString, selected=False)

    def _loadSceneFromXml(self, xmlString):
        self.pasteNodesFromXml(xmlString, selected=False)

    def setFile(self, path, reset=True):
        self.path = path
        self._loadSceneFromUng(path)

    @log_cost_time
    def resetScene(self, xmlString=''):
        self._beforeResetScene()

        if xmlString != '':
            self._loadSceneFromXml(xmlString)
        elif os.path.exists(self.path):
            self._loadSceneFromUng(self.path)

        self._afterResetScene()

    def _beforeResetScene(self):
        self.clear()
        self._allNodes = {}
        self._nodesSuffix = {}

    def _afterResetScene(self):
        self.view._resizeScene()
        self.frameSelection()

        logger.debug('scene nodeItem number: {}'.format(len(self.allNodes())))

    def createNode(self, nodeClass, name=None, pos=None, **kwargs):
        # QCoreApplication.processEvents()

        if nodeClass in Node.getAllNodeClassNames():
            if name is None:
                name = nodeClass
            nodeName, suffix, index = self._getUniqueName(name)
            nodeItem = NodeItem.createItem(
                nodeClass,
                name=nodeName,
                **kwargs
            )

            self.addItem(nodeItem)
            nodeItem.afterAddToScene()
            self._allNodes.update({nodeItem: nodeName})

            if pos is None:
                center = self.view.getCenterPos()
                pos = [center.x(), center.y()]
            nodeItem.setX(pos[0])
            nodeItem.setY(pos[1])

            if suffix in self._nodesSuffix:
                self._nodesSuffix[suffix].append(index)
            else:
                self._nodesSuffix[suffix] = [index]

            return nodeItem

    def connectAsChild(self, node, parentNode):
        self._addChildNode(node, parentNode)

    def selectAll(self):
        for node in self.allNodes():
            node.setSelected(True)

    def deleteSelection(self):
        self._deleteSelection()

    def _deleteSelection(self):
        selectedPipes = []
        selectedNodes = []
        for item in self.selectedItems():
            if isinstance(item, NodeItem):
                selectedNodes.append(item)
            elif isinstance(item, Pipe):
                selectedPipes.append(item)

        for pipe in selectedPipes:
            pipe.breakConnection()

        for node in selectedNodes:
            self.deleteNode(node)

    def deleteNode(self, node):
        pipes = []
        for port in node.ports:
            for pipe in port.pipes:
                if pipe not in pipes:
                    pipes.append(pipe)
        for pipe in pipes:
            pipe.breakConnection()
        self.removeItem(node)
        self._allNodes.pop(node)
        self.nodeDeleted.emit(node)

    def frameSelection(self):
        self.view.fitTo(self.selectedItems())

    def disableSelection(self):
        for node in self.getSelectedNodes():
            node.parameter('disable').setValue(1 - node.parameter('disable').getValue())

    def enterSelection(self):
        for item in self.selectedItems():
            if item.nodeObject.Class() in ['Import']:
                self.enterFileRequired.emit(item.parameter('path').getValue())
                return

    def updateSelectedNodesPipe(self):
        pipes = []
        for node in self.getSelectedNodes():
            for port in node.ports:
                for pipe in port.pipes:
                    if pipe not in pipes:
                        pipes.append(pipe)
        for pipe in pipes:
            pipe.updatePath()

    def allNodes(self):
        return list(self._allNodes.keys())

    def getNode(self, nodeName):
        nodes = self.allNodes()
        for node in nodes:
            if node.name() == nodeName:
                return node

    def getNodes(self, type=None):
        nodes = self.allNodes()
        if type is None:
            return nodes
        if not isinstance(type, (list, tuple)):
            type = [type]
        nodes = [n for n in nodes if n.nodeType in type]
        return nodes

    def getSelectedNodes(self):
        return [n for n in self.selectedItems() if isinstance(n, NodeItem)]

    def getNodesAsXml(self, nodes):
        rootElement = ET.Element('pynodegraph')
        nodesDict = {}
        if len(nodes) > 0:
            firstNode = nodes[0]
            minX = firstNode.parameter('x').getValue()
            minY = firstNode.parameter('y').getValue()
            for node in nodes:
                nodeElement = node.toXmlElement()
                rootElement.append(nodeElement)

                minX = min(node.parameter('x').getValue(), minX)
                minY = min(node.parameter('y').getValue(), minY)

            rootElement.set('x', str(minX))
            rootElement.set('y', str(minY))
            nodesString = convertToString(rootElement)
            return nodesString
        return ''

    def _exportNodesToFile(self, nodes, xmlfile):
        nodesString = self.getNodesAsXml(nodes)
        with open(xmlfile, 'w') as f:
            f.write(nodesString)

    def getSelectedNodesAsXml(self):
        nodes = self.getSelectedNodes()
        return self.getNodesAsXml(nodes)

    def getAllNodesAsXml(self):
        nodes = self.allNodes()
        return self.getNodesAsXml(nodes)

    def exportAllNodesToFile(self, xmlfile):
        nodes = self.allNodes()
        self._exportNodesToFile(nodes, xmlfile)

    def exportSelectedNodesToFile(self, xmlfile):
        nodes = self.getSelectedNodes()
        self._exportNodesToFile(nodes, xmlfile)

    def createParamFromXml(self, paramElement, node, offsetX=0, offsetY=0):
        paramName = paramElement.get('n')
        if paramName in ['name']:
            return

        custom = paramElement.get('cus', '0')
        visible = paramElement.get('vis', '1')
        parameterType = paramElement.get('t')
        value = paramElement.get('val')
        connect = paramElement.get('con')
        metadatas = paramElement.findall('m')
        hints = paramElement.findall('h')

        if node.hasParameter(paramName):
            parameter = node.parameter(paramName)
        else:
            parameter = node.addParameter(paramName, parameterType, custom=custom)

        if connect is not None:
            parameter.setConnect(connect)

        value = parameter.convertValueFromPy(value)
        if paramName == 'x':
            value = offsetX + value
            node.nodeObject.setProperty('x', value)
        elif paramName == 'y':
            value = offsetY + value
            node.nodeObject.setProperty('y', value)
        elif node.nodeObject.hasProperty(paramName):
            node.nodeObject.setProperty(paramName, value)
        elif paramName == 'label':
            value = value.replace('<\\n>', '\n')

        parameter.setValueQuietly(value)

        for metadataElement in metadatas:
            self.createMetadataFromXml(metadataElement, parameter)
        for hintElement in hints:
            self.createHintFromXml(hintElement, parameter)

    def createMetadataFromXml(self, metadataElement, obj):
        key = metadataElement.get('k')
        value = metadataElement.get('v')
        obj.setMetadata(key, value)

    def createHintFromXml(self, hintElement, obj):
        key = hintElement.get('k')
        value = hintElement.get('v')
        obj.setHint(key, value)

    def createNodeFromXml(self, nodeElement, _newNodes, _nameConvertDict, offsetX=0, offsetY=0):
        oldNodeName = nodeElement.get('n')
        nodeClass = nodeElement.get('c')
        node = self.createNode(nodeClass, name=oldNodeName)
        newName = node.parameter('name').getValue()

        _newNodes.append(node)
        _nameConvertDict.update({oldNodeName: newName})

        for paramElement in nodeElement.findall('p'):
            self.createParamFromXml(paramElement, node, offsetX, offsetY)

        for metadataElement in nodeElement.findall('m'):
            self.createMetadataFromXml(metadataElement, node)

        node.afterAddToScene()

    def createConnectFromXml(self, nodeElement, _nameConvertDict):
        oldNodeName = nodeElement.get('n')

        newNode = self.getNode(_nameConvertDict.get(oldNodeName))
        if newNode is None:
            return

        for outputElement in nodeElement.findall('o'):
            outputName = outputElement.get('n')
            sourceNodeName = outputElement.get('conN')
            sourceNodeInputName = outputElement.get('conP')

            sourceNode = self.getNode(_nameConvertDict.get(sourceNodeName))
            if sourceNode is None:
                sourceNode = self.getNode(sourceNodeName)
                if sourceNode is None:
                    continue
            sourceNode.connectSource(newNode, inputName=sourceNodeInputName, outputName=outputName)

        for inputElement in nodeElement.findall('i'):
            inputName = inputElement.get('n')
            sourceNodeName = inputElement.get('conN')
            sourceNodeOutputName = inputElement.get('conP')

            sourceNode = self.getNode(_nameConvertDict.get(sourceNodeName))
            if sourceNode is None:
                sourceNode = self.getNode(sourceNodeName)
                if sourceNode is None:
                    continue
            newNode.connectSource(sourceNode, inputName=inputName, outputName=sourceNodeOutputName)

    def createNodesFromXml(self, rootElement, offsetX=0, offsetY=0):
        _nameConvertDict = {}
        _newNodes = []
        for nodeElement in rootElement.getchildren():
            self.createNodeFromXml(
                nodeElement, _newNodes, _nameConvertDict,
                offsetX, offsetY
            )

        # connections
        for nodeElement in rootElement.getchildren():
            self.createConnectFromXml(nodeElement, _nameConvertDict)

        return _newNodes

    def pasteNodesFromXml(self, nodesString, selected=True):
        rootElement = ET.fromstring(nodesString)
        _topLeftX = float(rootElement.get('x'))
        _topLeftY = float(rootElement.get('y'))

        scenePos = self.view.mapToScene(self.view.clickedPos)
        offsetX = scenePos.x() - _topLeftX
        offsetY = scenePos.y() - _topLeftY

        nodes = self.createNodesFromXml(rootElement, offsetX, offsetY)
        if selected:
            for node in nodes:
                node.setSelected(True)

        return nodes

    def saveNodes(self):
        if self.path is None:
            xmlFile = QtWidgets.QFileDialog.getSaveFileName(None, 'Save', filter='PY Node Graph(*.pyng *.xml)')
            if isinstance(xmlFile, tuple):
                xmlFile = xmlFile[0]
            xmlFile = str(xmlFile)
            if xmlFile == '':
                return
            if not (xmlFile.endswith('.pyng') or xmlFile.endswith('.xml')):
                xmlFile += '.pyng'
            self.path = xmlFile
        self.exportAllNodesToFile(self.path)

    def execute(self):
        print('Execute nodes.')
        mainNode = self.getRootNode()
        if mainNode is None:
            return
        mainNode = mainNode.nodeObject
        mainNode.execute()

