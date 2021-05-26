# -*- coding: utf-8 -*-

import traceback
import re
from pyNodeGraph.module.sqt import *
from pyNodeGraph.ui.graph.other.port import (
    InputPort, OutputPort, ParameterInputPort, ParameterOutputPort, FlowInputPort, FlowOutputPort, FlowData,
    DotFInputPort, DotFOutputPort, DotPInputPort, DotPOutputPort
)
from pyNodeGraph.ui.graph.other.pipe import Pipe, ParameterPipe
from ..const import *
from pyNodeGraph.utils.log import get_logger
from pyNodeGraph.core.node import Node
from pyNodeGraph.core.parameter.basic import Parameter
from pyNodeGraph.core.parameter.params import ObjectParameter
from pyNodeGraph.ui.graph.other.tag import LockTag
from pyNodeGraph.core.state import GraphState

logger = get_logger('pyNodeGraph.nodeItem')


NODE_HEIGHT_BASE = 20
NAME_FONT = QtGui.QFont('Arial', 10, italic=True)
NAME_FONT.setBold(True)
LABEL_FONT = QtGui.QFont('Arial', 10)

EXPRESSION_VALUE_PATTERN = re.compile(r'\[value [^\[\]]+\]')
EXPRESSION_PYTHON_PATTERN = re.compile(r'\[python [^\[\]]+\]')


class _BaseNodeItem(QtWidgets.QGraphicsItem):
    x = 0
    y = 0
    w = 150
    h = NODE_HEIGHT_BASE

    labelNormalColor = QtGui.QColor(200, 200, 200)
    labelHighlightColor = QtGui.QColor(40, 40, 40)

    disablePenColor = QtGui.QColor(150, 20, 20)

    def __init__(self, nodeObjectClass, **kwargs):
        super(_BaseNodeItem, self).__init__()

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.pipes = []
        self.ports = []
        self.tags = {}
        self.panel = None

        self.margin = 6
        self.roundness = 10

        self._initUI()

        self.nodeObject = nodeObjectClass(item=self, **kwargs)

        self.fillColor = QtGui.QColor(*self.getParamColor('fillColor'))
        self.borderColor = QtGui.QColor(*self.getParamColor('borderColor'))

        self.nodeObject.parameterValueChanged.connect(self._paramterValueChanged)

    def getParamColor(self, param):
        color = self.parameter(param).getValue()
        return self.nodeObject.convertColorTo255(color)

    def parameter(self, parameterName):
        return self.nodeObject.parameter(parameterName)

    def hasParameter(self, name):
        return self.nodeObject.hasParameter(name)

    def parameters(self):
        return self.nodeObject.parameters()

    def addParameter(self, *args, **kwargs):
        return self.nodeObject.addParameter(*args, **kwargs)

    def setMetadata(self, *args, **kwargs):
        self.nodeObject.setMetadata(*args, **kwargs)

    def Class(self):
        return self.nodeObject.Class()

    def name(self):
        return self.nodeObject.name()

    def _getInputsList(self):
        inputs = []
        for inputPort in self.getInputPorts():
            if len(inputPort.getConnections()) > 0:
                for outputPort in inputPort.getConnections():
                    node = outputPort.node()
                    inputs.append([inputPort.name, node.name(), outputPort.name])
        return inputs

    def _getOutputsList(self):
        outputs = []
        for outputPort in self.getOutputPorts():
            if len(outputPort.getConnections()) > 0:
                for inputPort in outputPort.getConnections():
                    node = inputPort.node()
                    outputs.append([outputPort.name, node.name(), inputPort.name])
        return outputs

    def toXmlElement(self):
        from pyNodeGraph.core.parse._xml import ET

        nodeElement = ET.Element('n')
        nodeElement.set('n', self.parameter('name').getValue())
        nodeElement.set('c', self.Class())

        for paramName, param in self.nodeObject._parameters.items():
            if paramName != 'name':
                override = param.isOverride()
                custom = param.isCustom()

                if not (override or custom) and not self.nodeObject.hasProperty(paramName):
                    continue

                paramElement = param.toXmlElement()
                nodeElement.append(paramElement)

        inputs = self._getInputsList()
        outputs = self._getOutputsList()

        for outputName, nodeName, inputName in outputs:
            outputElement = ET.Element('o')
            outputElement.set('n', outputName)
            outputElement.set('conN', nodeName)
            outputElement.set('conP', inputName)
            nodeElement.append(outputElement)

        for inputName, nodeName, outputName in inputs:
            inputElement = ET.Element('i')
            inputElement.set('n', inputName)
            inputElement.set('conN', nodeName)
            inputElement.set('conP', outputName)
            nodeElement.append(inputElement)

        for key, value in self.nodeObject.getMetadatas().items():
            metadataElement = ET.Element('m')
            metadataElement.set('k', key)
            metadataElement.set('v', value)
            nodeElement.append(metadataElement)

        return nodeElement

    def toXml(self):
        from pyNodeGraph.core.parse._xml import convertToString

        element = self.toXmlElement()
        return convertToString(element)

    @property
    def nodeType(self):
        return self.nodeObject.nodeType

    def _initUI(self):
        self.nameItem = None
        self.disableItem = None

    def _updateNameText(self):
        if self.nameItem is not None:
            name = self.parameter('name').getValue()
            self.nameItem.setText(name)
            self._updateNamePos()

    def _updateNamePos(self):
        rect = self.nameItem.boundingRect()
        self.nameItem.setX((self.w - rect.width()) / 2.0)
        self.nameItem.setY((self.h - rect.height()) / 2.0 - 10)

    def _updateDisableItem(self):
        disable = self.parameter('disable').getValue()
        if self.disableItem is None:
            self.disableItem = QtWidgets.QGraphicsLineItem(self)
            self.disablePen = QtGui.QPen(self.disablePenColor)
            self.disablePen.setWidth(5)
            self.disableItem.setPen(self.disablePen)
        self.disableItem.setLine(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(self.w, self.h)
        ))
        self.disableItem.setVisible(disable)

    def _updateLockTag(self):
        if self.nodeObject.isNodeLocked():
            self.addTag('lock', LockTag(), position=0.5)
        else:
            self.removeTag('lock')

    def _paramterValueChanged(self, parameter):
        if parameter.name() == 'x':
            self.setX(parameter.getValue())
        if parameter.name() == 'y':
            self.setY(parameter.getValue())
        if parameter.name() == 'disable':
            self._updateDisableItem()
        if parameter.name() == 'locked':
            self._updateLockTag()
        if parameter.name() == 'name':
            self._updateNameText()
        if parameter.name() in ['fillColor', 'borderColor']:
            self.update()
        # self._updateUI()

    def setLabelVisible(self, visible):
        if not visible and self.nameItem is None:
            return
        if visible and self.nameItem is None:
            self.nameItem = QtWidgets.QGraphicsSimpleTextItem(self)
            self.nameItem.setFont(NAME_FONT)
            self.nameItem.setBrush(DEFAULT_LABEL_COLOR)
        self.nameItem.setVisible(visible)
        if visible:
            self._updateNameText()

    def setPortsLabelVisible(self, visible):
        for port in self.ports:
            port.setLabelVisible(visible)

    def updateUI(self):
        self._updateUI()

    def _updateUI(self):
        self._updateLockTag()
        self._updateNameText()

    def forceUpdatePanelUI(self):
        if self.panel is not None:
            self.panel.updateUI()

    def _portConnectionChanged(self, port):
        if isinstance(port, ParameterInputPort):
            parameter = self.parameter(port.name)
            if parameter is None:
                return
            connections = port.getConnections()
            if len(connections) == 0:
                parameter.breakConnect()
            elif len(connections) == 1:
                connectPort = connections[0]
                connectNode = connectPort.node()
                connectPath = '{}.{}'.format(connectNode.name(), connectPort.name)
                parameter.setConnect(connectPath)
            else:
                logger.warning('Input Port {}.{} has more than one connection!'.format(self.name(), port.name))


    def connectSource(self, node, inputName='input', outputName='output'):
        """
        input -> output
        :param node:
        :param inputName:
        :param outputName:
        :return:
        """
        inputPort = self.getInputPort(inputName)
        if inputPort is None:
            logger.warning('Input Port Not Exist! {}:{}'.format(node.name(), inputName))
            return

        outputPort = node.getOutputPort(outputName)
        if outputPort is None:
            logger.warning('Output Port Not Exist! {}{}'.format(node.name(), outputName))
            return

        inputPort.connectTo(outputPort)

    # def connectDestination(self, nodeItem, outputName='', inputName=''):
    #     pass

    def getInputPorts(self):
        return [port for port in self.ports if isinstance(port, InputPort)]

    def getOutputPorts(self):
        return [port for port in self.ports if isinstance(port, OutputPort)]

    def getInputPort(self, portName):
        for port in self.getInputPorts():
            if port.name == portName:
                return port

    def getOutputPort(self, portName):
        for port in self.getOutputPorts():
            if port.name == portName:
                return port

    def getPort(self, portName):
        for port in self.ports:
            if port.name == portName:
                return port

    def addPort(self, port):
        port.setParentItem(self)
        self.ports.append(port)
        port.portObj.connectChanged.connect(self._portConnectionChanged)

    def removePort(self, port):
        self.ports.remove(port)
        self.scene().removeItem(port)

    def addTag(self, name, tagItem, position=0.0):
        if name not in self.tags:
            self._addTag(name, tagItem, position=position)
        else:
            self.tags[name].setVisible(True)

    def _addTag(self, name, tagItem, position=0.0):
        tagItem.setParentItem(self)
        margin_x = tagItem.w / 2.0 + TAG_MARGIN
        margin_y = tagItem.h / 2.0 + TAG_MARGIN
        if position <= 0.25:
            y = 0 - margin_y
            x = position * (self.w + margin_x * 2) / 0.25 - margin_x
        elif 0.25 < position <= 0.5:
            x = (self.w + margin_x * 2) - margin_x
            y = (position - 0.25) * (self.h + margin_y * 2.0) / 0.25 - margin_y
        elif 0.5 < position <= 0.75:
            x = (position - 0.5) * (-2.0 * margin_x - self.w) / 0.25 + (self.w + margin_x)
            y = self.h + margin_y
        elif 0.75 < position <= 1.0:
            x = 0 - margin_x
            y = (position - 0.75) * (-2.0 * margin_y - self.h) / 0.25 + (self.h + margin_y)
        tagItem.setPos(x - tagItem.w / 2.0, y - tagItem.h / 2.0)
        self.tags[name] = tagItem

    def removeTag(self, name):
        if name in self.tags:
            tag = self.tags[name]
            tag.setVisible(False)

    def setHighlight(self, value=True):
        self.fillColor = QtGui.QColor(*self.nodeObject.fillHighlightColor) if value else QtGui.QColor(*self.getParamColor('fillColor'))
        self.borderColor = QtGui.QColor(*self.nodeObject.borderHighlightColor) if value else QtGui.QColor(*self.getParamColor('borderColor'))
        if self.nameItem is not None:
            self.nameItem.setBrush(self.labelHighlightColor if value else self.labelNormalColor)

    def updatePipe(self):
        for port in self.ports:
            for pipe in port.pipes:
                pipe.updatePath()

    def getContextMenus(self):
        actions = self.nodeObject.getActions()
        return actions

    def boundingRect(self):
        rect = QtCore.QRectF(
            self.x,
            self.y,
            self.w,
            self.h)

        return rect

    def paint(self, painter, option, widget):
        if self.isSelected():
            penWidth = 2
        else:
            penWidth = 5
        self.setHighlight(self.isSelected())

        pen = QtGui.QPen(self.borderColor)
        pen.setWidth(penWidth)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(self.fillColor))

        painter.drawRoundedRect(self.x, self.y, self.w, self.h, self.roundness, self.roundness)

    def mouseMoveEvent(self, event):
        self.scene().updateSelectedNodesPipe()
        super(_BaseNodeItem, self).mouseMoveEvent(event)
        # slow
        # for n in self.scene().getSelectedNodes():
        #     n.parameter('x').setValue(n.scenePos().x())
        #     n.parameter('y').setValue(n.scenePos().y())

    def mouseDoubleClickEvent(self, event):
        super(_BaseNodeItem, self).mouseDoubleClickEvent(event)
        self.scene().parent().itemDoubleClicked.emit(self)

    def hoverEnterEvent(self, event):
        super(_BaseNodeItem, self).hoverEnterEvent(event)
        self.setToolTip(self.getToolTip())

    def getToolTip(self):
        return self.parameter('name').getValue()


class NodeItem(_BaseNodeItem):
    _nodeItemsMap = {}
    nodeItemType = 'NodeItem'

    @classmethod
    def createItem(cls, nodeType, **kwargs):
        nodeClass = Node.getNodeClass(nodeType)
        nodeItemClass = cls._nodeItemsMap.get(nodeClass.nodeItemType)
        item = nodeItemClass(nodeClass, **kwargs)
        return item

    @classmethod
    def registerNodeItem(cls, itemClass):
        cls._nodeItemsMap.update(
            {itemClass.nodeItemType: itemClass}
        )

    def __init__(self, *args, **kwargs):
        self.inputParameterPorts = []
        self.outputParameterPorts = []
        self.inputFlowPorts = []
        self.outputFlowPorts = []

        self.findPipes = []

        super(NodeItem, self).__init__(*args, **kwargs)

    def _initUI(self):
        super(NodeItem, self)._initUI()

        self.labelItem = None

    def _updateLabelText(self):
        if self.labelItem is None:
            return

        label = self.parameter('label').getValue()
        labelFontSize = self.parameter('labelFontSize').getValue()

        expStrings = re.findall(EXPRESSION_VALUE_PATTERN, label)
        for expString in expStrings:
            paramName = ' '.join(expString.split(' ')[1:]).replace(']', '')
            param = self.parameter(paramName)
            if param is not None:
                paramValue = param.getValue()
                label = label.replace(expString, str(paramValue))

        expStrings = re.findall(EXPRESSION_PYTHON_PATTERN, label)
        for expString in expStrings:
            pyString = ' '.join(expString.split(' ')[1:]).replace(']', '')
            try:
                result = eval(pyString, globals(), Node._expressionMap)
            except(Exception) as e:
                result = e
            label = label.replace(expString, str(result))

        label = label.replace('\n', '<p>')
        self.labelItem.setHtml(label)
        font = QtGui.QFont('Arial', labelFontSize)
        self.labelItem.setFont(font)
        self._updateLabelPos()

    def _updateLabelPos(self):
        rect = self.labelItem.boundingRect()
        self.labelItem.setX((self.w - rect.width()) / 2.0)
        self.labelItem.setY(self.h / 2.0 + 0)

    def setLabelVisible(self, visible):
        super(NodeItem, self).setLabelVisible(visible)
        if not visible and self.labelItem is None:
            return
        if visible and self.labelItem is None:
            self.labelItem = QtWidgets.QGraphicsTextItem(self)
            self.labelItem.setFont(LABEL_FONT)
        self.labelItem.setVisible(visible)
        if visible:
            self._updateLabelText()

    def _paramterValueChanged(self, parameter):
        super(NodeItem, self)._paramterValueChanged(parameter)
        if parameter.name() == 'label':
            self._updateLabelText()

    def _updateUI(self):
        super(NodeItem, self)._updateUI()
        self._updateLockTag()
        self._updateNameText()
        self._updateLabelText()

    def _updateHeight(self):
        inputsNum = len(self.inputParameterPorts) + len(self.inputFlowPorts)
        outputsNum = len(self.outputParameterPorts) + len(self.outputFlowPorts)
        self.h = NODE_HEIGHT_BASE
        self.h += PORT_SPACING * max(inputsNum, outputsNum)

    def addFlowPort(self, port):
        self.addPort(port)
        self._updateHeight()
        self.updateFlowPortsPos()

    def addFlowInputPort(self, portName):
        port = FlowInputPort(name=portName)
        self.inputFlowPorts.append(port)
        self.addFlowPort(port)

    def addFlowOutputPort(self, portName):
        port = FlowOutputPort(name=portName)
        self.outputFlowPorts.append(port)
        self.addFlowPort(port)

    def updateFlowPortsPos(self):
        bbox = self.boundingRect()

        for index, port in enumerate(self.inputFlowPorts):
            port.setPos(
                bbox.left() - port.w / 2.0,
                10 + index * PORT_SPACING
            )
        for index, port in enumerate(self.outputFlowPorts):
            port.setPos(
                bbox.right() - port.w + port.w / 2.0,
                10 + index * PORT_SPACING
            )

    def addParameterPort(self, port):
        self.addPort(port)
        self._updateHeight()
        self.updateParameterPortsPos()

    def addParameterInputPort(self, portName, label=None, dataType=None):
        port = ParameterInputPort(name=portName, label=label, dataType=dataType)
        self.inputParameterPorts.append(port)
        self.addParameterPort(port)

    def addParameterOutputPort(self, portName, label=None, dataType=None):
        port = ParameterOutputPort(name=portName, label=label, dataType=dataType)
        self.outputParameterPorts.append(port)
        self.addParameterPort(port)

    def removeParameterPort(self, portName):
        port = self.getPort(portName)
        if port is None:
            return
        if port in self.inputParameterPorts:
            self.inputParameterPorts.remove(port)
        if port in self.outputParameterPorts:
            self.outputParameterPorts.remove(port)
        self.removePort(port)
        self._updateHeight()
        self.updateParameterPortsPos()

    def updateParameterPortsPos(self):
        bbox = self.boundingRect()

        for index, port in enumerate(self.inputParameterPorts):
            port.setPos(
                bbox.left() - port.w / 2.0,
                max(len(self.inputFlowPorts), 0) * PORT_SPACING + (index + 1) * PORT_SPACING
            )
        for index, port in enumerate(self.outputParameterPorts):
            port.setPos(
                bbox.right() - port.w + port.w / 2.0,
                len(self.outputFlowPorts) * PORT_SPACING + (index + 1) * PORT_SPACING
            )

    def afterAddToScene(self):
        pass

    def _getFindPipes(self):
        findPipes = [
            item for item in self.collidingItems(QtCore.Qt.IntersectsItemShape)
            if isinstance(item, Pipe) and not isinstance(item, ParameterPipe)
        ]
        return findPipes

    def _findPipeToConnect(self):
        findPipes = self._getFindPipes()

        if len(self.findPipes) > 0:
            for pipe in self.findPipes:
                pipe.setLineColor(highlight=False)
                pipe.update()
                self.findPipes = []

        if len(findPipes) > 0:
            self.findPipes = findPipes
            for pipe in self.findPipes:
                pipe.setLineColor(highlight=True)
                pipe.update()

    def _connectToFoundPipe(self):
        if len(self.findPipes) > 0:
            for pipe in self.findPipes:
                source = pipe.source
                target = pipe.target

                pipe.breakConnection()

                self.inputFlowPorts[0].connectTo(source)
                self.outputFlowPorts[0].connectTo(target)

            self.findPipes = []

    def mousePressEvent(self, event):
        super(NodeItem, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.findingPipe = True
            self.startPos = self.mapToScene(self.boundingRect().center())

    def mouseMoveEvent(self, event):
        super(NodeItem, self).mouseMoveEvent(event)

        connectedPipes = []
        for port in self.ports:
            connectedPipes.extend(port.pipes)

        if len(self.inputFlowPorts) != 0 and len(connectedPipes) == 0:
            # if already has connect, don't find other pipe
            self._findPipeToConnect()

    def mouseReleaseEvent(self, event):
        super(NodeItem, self).mouseReleaseEvent(event)
        self._connectToFoundPipe()


class DotNodeItem(NodeItem):
    nodeItemType = 'DotItem'
    x = 0
    y = 0
    w = 20
    h = 20

    def setLabelVisible(self, visible):
        super(DotNodeItem, self).setLabelVisible(False)

    def __init__(self, *args, **kwargs):
        super(DotNodeItem, self).__init__(*args, **kwargs)
        self.initPorts()
        self.setDotPorts()

    def initPorts(self):
        self.inputPort = InputPort(name='i', dataType=Parameter)
        self.outputPort = OutputPort(name='o', dataType=Parameter)

    def setDotPorts(self):
        bbox = self.boundingRect()
        self.inputPort.setPos(
            bbox.left() - self.inputPort.w / 2.0,
            bbox.height() / 2.0 - self.inputPort.h / 2.0
        )
        self.outputPort.setPos(
            bbox.width() - self.outputPort.w / 2.0,
            bbox.height() / 2.0 - self.outputPort.h / 2.0
        )

        self.addPort(self.inputPort)
        self.addPort(self.outputPort)

    def _getFindPipes(self):
        findPipes = [
            item for item in self.collidingItems(QtCore.Qt.IntersectsItemShape)
            if isinstance(item, Pipe)
        ]
        return findPipes

    def mouseMoveEvent(self, event):
        super(DotNodeItem, self).mouseMoveEvent(event)

        connectedPipes = []
        for port in self.ports:
            connectedPipes.extend(port.pipes)

        if len(connectedPipes) == 0:
            # if already has connect, don't find other pipe
            self._findPipeToConnect()

    def _connectToFoundPipe(self):
        if len(self.findPipes) > 0:
            if self.nodeItemType == 'DotItem':
                pipe = self.findPipes[0]
                if isinstance(pipe, ParameterPipe):
                    c = 'DotP'
                else:
                    c = 'DotF'
                newDot = self.scene().createNode(c, pos=[self.pos().x(), self.pos().y()])
            else:
                newDot = self

            for pipe in self.findPipes:
                source = pipe.source
                target = pipe.target

                pipe.breakConnection()

                newDot.inputPort.connectTo(source)
                newDot.outputPort.connectTo(target)

            self.findPipes = []

            if newDot != self:
                self.scene().removeItem(self)


class FlowDotItem(DotNodeItem):
    nodeItemType = 'FlowDotItem'
    def initPorts(self):
        self.inputPort = DotFInputPort(name='i', dataType=FlowData)
        self.outputPort = DotFOutputPort(name='o', dataType=FlowData)

    def _getFindPipes(self):
        findPipes = [
            item for item in self.collidingItems(QtCore.Qt.IntersectsItemShape)
            if isinstance(item, Pipe) and not isinstance(item, ParameterPipe)
        ]
        return findPipes


class ParameterDotItem(DotNodeItem):
    nodeItemType = 'ParameterDotItem'
    def initPorts(self):
        self.inputPort = DotPInputPort(name='i', dataType=ObjectParameter)
        self.outputPort = DotPOutputPort(name='o', dataType=ObjectParameter)

    def _getFindPipes(self):
        findPipes = [
            item for item in self.collidingItems(QtCore.Qt.IntersectsItemShape)
            if isinstance(item, ParameterPipe)
        ]
        return findPipes


class BackdropNodeItem(NodeItem):
    nodeItemType = 'BackdropItem'
    _minSize = 80, 80
    w = 80
    h = 80

    def __init__(self, *args, **kwargs):
        super(BackdropNodeItem, self).__init__(*args, **kwargs)

        self.topRectItem = QtWidgets.QGraphicsRectItem(self)
        color = QtGui.QColor(self.fillColor)
        pen = QtGui.QPen(color)
        pen.setWidth(0)
        self.topRectItem.setBrush(color)
        self.topRectItem.setPen(pen)

        self._sizer = BackdropSizeChanger(self)
        self.setSizerPos()

        self._nodes = []

        self.selecting = False
        self.moving = False
        self.selectStart = QtCore.QPointF(0, 0)
        self.roundness = 0

    def setSizerPos(self):
        x = self.w - self._sizer.size
        y = self.h - self._sizer.size
        self._sizer.setPos(x, y)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._nodes = [self]
            for node in self.getContainNodes():
                if node.zValue() <= self.zValue():
                    node.setZValue(self.zValue() + 1)
            if event.pos().y() <= 20 or event.modifiers() == QtCore.Qt.ShiftModifier:
                self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
                self.moving = True

                self.scene().clearSelection()

                if event.modifiers() != QtCore.Qt.ControlModifier:
                    self._nodes += self.getContainNodes(False)
                [n.setSelected(True) for n in self._nodes]
            else:
                self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
                self.selecting = True
                self.selectStart = event.scenePos()
                self._nodes += self.getContainNodes(False)
                [n.setSelected(False) for n in self._nodes]
                self._sizer.setSelected(False)

    def mouseReleaseEvent(self, event):
        super(BackdropNodeItem, self).mouseReleaseEvent(event)
        self.setFlag(self.ItemIsMovable, True)
        if not self.selecting:
            [n.setSelected(True) for n in self._nodes]
        self._nodes = []
        self.selecting = False
        self.moving = False

    def mouseMoveEvent(self, event):
        if self.moving:
            super(BackdropNodeItem, self).mouseMoveEvent(event)
        if self.selecting:
            pos = event.scenePos()
            x = min(self.selectStart.x(), pos.x())
            y = min(self.selectStart.y(), pos.y())
            w = abs(self.selectStart.x() - pos.x())
            h = abs(self.selectStart.y() - pos.y())
            rect = QtCore.QRectF(x, y, w, h)
            items = self.scene().items(rect)
            for item in items:
                item.setSelected(True)

    def sizerPosChanged(self, pos):
        self.w = pos.x() + self._sizer.size
        self.h = pos.y() + self._sizer.size
        self.topRectItem.setRect(0, 0, self.w - 2, 20.0)

    def getContainNodes(self, inc_intersects=False):
        mode = {True: QtCore.Qt.IntersectsItemShape,
                False: QtCore.Qt.ContainsItemShape}
        nodes = []
        if self.scene():
            polygon = self.mapToScene(self.boundingRect())
            rect = polygon.boundingRect()
            items = self.scene().items(rect, mode=mode[inc_intersects])
            for item in items:
                if item == self or item == self._sizer:
                    continue
                if not isinstance(item, BackdropSizeChanger) and isinstance(item, NodeItem):
                    nodes.append(item)
        return nodes

    def _updateNamePos(self):
        rect = self.nameItem.boundingRect()
        self.nameItem.setX((self.w - rect.width()) / 2.0)
        self.nameItem.setY(0)

    def _updateLabelPos(self):
        rect = self.labelItem.boundingRect()
        self.labelItem.setX(0)
        self.labelItem.setY(24)

    def setLabelVisible(self, visible):
        super(BackdropNodeItem, self).setLabelVisible(True)

    def _paramterValueChanged(self, parameter):
        super(BackdropNodeItem, self)._paramterValueChanged(parameter)
        if parameter.name() == 'width':
            self.w = parameter.getValue()
        if parameter.name() == 'height':
            self.h = parameter.getValue()


class BackdropSizeChanger(QtWidgets.QGraphicsItem):
    size = 20

    def __init__(self, parent=None):
        super(BackdropSizeChanger, self).__init__(parent)
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QtCore.Qt.SizeFDiagCursor)

    def boundingRect(self):
        return QtCore.QRectF(0.5, 0.5, self.size, self.size)

    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            try:
                value = value.toPointF()
            except:
                pass
            value = self.posChanged(value)
            return value
        return super(BackdropSizeChanger, self).itemChange(change, value)

    def posChanged(self, value):
        item = self.parentItem()
        mx, my = item._minSize
        x = mx if value.x() < mx else value.x()
        y = my if value.y() < my else value.y()
        value = QtCore.QPointF(x, y)
        item.sizerPosChanged(value)
        return value

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.scene().clearSelection()
            self.setSelected(True)
        super(BackdropSizeChanger, self).mousePressEvent(event)

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        item = self.parentItem()
        color = QtGui.QColor(item.fillColor)
        color = color.darker(110)
        path = QtGui.QPainterPath()
        path.moveTo(rect.topRight())
        path.lineTo(rect.bottomRight())
        path.lineTo(rect.bottomLeft())
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.fillPath(path, painter.brush())


NodeItem.registerNodeItem(DotNodeItem)
NodeItem.registerNodeItem(FlowDotItem)
NodeItem.registerNodeItem(ParameterDotItem)
NodeItem.registerNodeItem(BackdropNodeItem)

