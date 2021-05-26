# -*- coding: utf-8 -*-


from pyNodeGraph.module.sqt import *
from pyNodeGraph.ui.graph.other.pipe import Pipe, ParameterPipe
from pyNodeGraph.core.state import GraphState
from pyNodeGraph.core.parameter.basic import Parameter

PORT_SIZE = 10
PORT_LABEL_COLOR = QtGui.QColor(200, 200, 200)


class PortObject(QtCore.QObject):
    connectChanged = QtCore.Signal(object)

    def __init__(self, item=None, *args, **kwargs):
        super(PortObject, self).__init__(*args, **kwargs)

        self._item = item

    def _connectChanged(self):
        self.connectChanged.emit(self._item)


class Port(QtWidgets.QGraphicsEllipseItem):
    orientation = 0
    x = 0
    y = 0
    w = PORT_SIZE
    h = PORT_SIZE

    fillColor = QtGui.QColor(230, 230, 0)
    borderNormalColor = QtGui.QColor(200, 200, 250)
    borderHighlightColor = QtGui.QColor(255, 255, 0)

    borderNormalWidth = 1
    borderHighlightWidth = 3

    maxConnections = None

    def __init__(self, name='input', label=None, dataType=None, **kwargs):
        super(Port, self).__init__(**kwargs)

        self.portObj = PortObject(self)
        self.name = name
        self.dataType = dataType
        self.label = label if label is not None else name
        self.pipes = []

        self.findingPort = False
        self.foundPort = None

        if issubclass(self.dataType, Parameter):
            if self.dataType.borderNormalColor is not None:
                self.borderNormalColor = QtGui.QColor(*self.dataType.borderNormalColor)
            if self.dataType.fillNormalColor is not None:
                self.fillColor = QtGui.QColor(*self.dataType.fillNormalColor)

        self.borderColor = self.borderNormalColor
        self.borderWidth = self.borderNormalWidth

        self.nameItem = None

        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAcceptDrops(True)
        self.setZValue(10)

        self.setToolTip('{}\n{}'.format(self.name, str(self.dataType.parameterTypeString)))

        self.setRect(self.boundingRect())
        self._updateUI()

    def _updateUI(self):
        pen = QtGui.QPen(self.borderColor)
        pen.setWidth(self.borderWidth)
        self.setPen(pen)
        self.setBrush(QtGui.QBrush(self.fillColor))

    def setLabelVisible(self, visible):
        if not visible and self.nameItem is None:
            return
        if visible and self.nameItem is None:
            self.nameItem = QtWidgets.QGraphicsSimpleTextItem(self)
            self.nameItem.setBrush(PORT_LABEL_COLOR)
            self.nameItem.setText(self.label)
            self.nameRect = self.nameItem.boundingRect()
            self.nameTransform = QtGui.QTransform()
            self._setNameTransform()
            self.nameItem.setTransform(self.nameTransform)
        self.nameItem.setVisible(visible)

    def _setNameTransform(self):
        pass

    def node(self):
        return self.parentItem()

    def connectTo(self, port, emitSignal=True, connection=False):
        """
        inputPort -> outputPort
        :param port:
        :return:
        """
        if port is self:
            return

        for pipe in self.pipes:
            if (pipe.source == self and pipe.target == port) or (pipe.source == port and pipe.target == self):
                pipe.updatePath()
                return

        self._checkConnectionNumber()
        port._checkConnectionNumber()

        pipe = self.createPipe()
        if isinstance(self, InputPort):
            pipe.source = port
            pipe.target = self
        else:
            pipe.source = self
            pipe.target = port

        self.addPipe(pipe, emitSignal=emitSignal)
        port.addPipe(pipe, emitSignal=emitSignal)

        self.scene().addItem(pipe)

        pipe.updatePath()

    def addPipe(self, pipe, emitSignal=True):
        self.pipes.append(pipe)
        if emitSignal:
            self.portObj._connectChanged()

    def removePipe(self, pipe):
        if pipe in self.pipes:
            self.pipes.remove(pipe)
            self.portObj._connectChanged()

    def _checkConnectionNumber(self):
        if self.maxConnections is None:
            return
        if len(self.pipes) == self.maxConnections:
            pipe = self.pipes[0]
            self.removePipe(pipe)
            pipe.breakConnection()

    def boundingRect(self):
        rect = QtCore.QRectF(
            self.x,
            self.y,
            self.w,
            self.h
        )
        return rect

    def setHighlight(self, toggle):
        if toggle:
            self.borderColor = self.borderHighlightColor
            self.borderWidth = self.borderHighlightWidth
        else:
            self.borderColor = self.borderNormalColor
            self.borderWidth = self.borderNormalWidth
        self._updateUI()

    def destroy(self):
        pipesToDelete = self.pipes[::]  # Avoid shrinking during deletion.
        for pipe in pipesToDelete:
            self.removePipe(pipe)
            self.scene().removeItem(pipe)
        node = self.node()
        if node:
            node.removePort(self)

        self.scene().removeItem(self)
        del self

    def createPipe(self):
        if isinstance(self, (ParameterInputPort, ParameterOutputPort)):
            pipe = ParameterPipe(orientation=self.orientation, dataType=self.dataType)
        else:
            pipe = Pipe(orientation=self.orientation, dataType=self.dataType)
        return pipe

    @classmethod
    def canConnect(cls, port1, port2):
        if isinstance(port1, port2.__class__):
            return False

        if port1.io == port2.io:
            return False

        input = None
        output = None
        if port1.io == 0:
            input = port1
            output = port2
        else:
            input = port2
            output = port1

        dataTypeSupport = False
        if input.dataType == output.dataType:
            dataTypeSupport = True
        elif issubclass(output.dataType, input.dataType) or issubclass(input.dataType, output.dataType):
            dataTypeSupport = True

        return dataTypeSupport

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.findingPort = True
            # self.startPos = self.scenePos()
            self.startPos = self.mapToScene(self.boundingRect().center())
            self.floatPipe = self.createPipe()
            self.scene().addItem(self.floatPipe)

    def mouseMoveEvent(self, event):
        if self.findingPort:
            pos = event.pos()
            pos = pos - QtCore.QPointF(self.w / 2.0, self.h / 2.0)
            scenePos = self.startPos + pos
            if isinstance(self, InputPort):
                self.floatPipe.updatePath(scenePos, self.startPos)
            elif isinstance(self, OutputPort):
                self.floatPipe.updatePath(self.startPos, scenePos)

            findPort = self.scene().itemAt(scenePos, QtGui.QTransform())

            if (
                    findPort is not None
                    and isinstance(findPort, Port)
                    and self.canConnect(self, findPort)
            ):
                self.foundPort = findPort
                self.foundPort.setHighlight(True)
            else:
                if self.foundPort is not None:
                    self.foundPort.setHighlight(False)
                    self.foundPort = None

    def _connectToFoundPort(self, event):
        pos = event.pos()
        pos = pos - QtCore.QPointF(self.w / 2.0, self.h / 2.0)
        scenePos = self.startPos + pos
        findPort = self.scene().itemAt(scenePos, QtGui.QTransform())
        if (
                findPort is not None
                and isinstance(findPort, Port)
                and self.canConnect(self, findPort)
        ):
            if self.name != findPort.name:
                self.connectTo(findPort)
        self.scene().removeItem(self.floatPipe)

        self.findingPort = False
        if self.foundPort is not None:
            self.foundPort.setHighlight(False)
            self.foundPort = None

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.findingPort:
            self._connectToFoundPort(event)

    def getContextMenus(self):
        actions = [
            ['remove_port', 'Remove Port', None, self._removePortTriggered],
        ]
        return actions

    def _removePortTriggered(self):
        self.node().nodeObject.removeParameter(self.name)


class InputPort(Port):
    orientation = 1
    maxConnections = 1

    io = 0

    def _setNameTransform(self):
        self.nameTransform.translate(
            self.w + 5,
            -(self.nameRect.height() / 2.0 - self.h / 2.0)
        )

    def getConnections(self):
        return [pipe.source for pipe in self.pipes if pipe.target == self and pipe.source is not None]


class OutputPort(Port):
    orientation = 1

    io = 1

    def _setNameTransform(self):
        self.nameTransform.translate(
            -self.nameRect.width() - 5,
            -(self.nameRect.height() / 2.0 - self.h / 2.0)
        )

    def getConnections(self):
        return [pipe.target for pipe in self.pipes if pipe.source == self]


class FlowData(Parameter):
    parameterTypeString = '<>'


class FlowInputPort(InputPort):
    borderNormalWidth = 2
    borderNormalColor = QtGui.QColor(230, 230, 230)
    fillColor = QtGui.QColor(30, 30, 30)
    w = PORT_SIZE + 5
    h = PORT_SIZE + 5
    maxConnections = None

    def __init__(self, *args, **kwargs):
        if 'dataType' not in kwargs:
            kwargs['dataType'] = FlowData
        super(FlowInputPort, self).__init__(*args, **kwargs)


class FlowOutputPort(OutputPort):
    borderNormalWidth = 2
    borderNormalColor = QtGui.QColor(230, 230, 230)
    fillColor = QtGui.QColor(30, 30, 30)
    w = PORT_SIZE + 5
    h = PORT_SIZE + 5

    def __init__(self, *args, **kwargs):
        if 'dataType' not in kwargs:
            kwargs['dataType'] = FlowData
        super(FlowOutputPort, self).__init__(*args, **kwargs)


class ParameterInputPort(InputPort):
    borderNormalColor = QtGui.QColor(80, 120, 200)


class ParameterOutputPort(OutputPort):
    borderNormalColor = QtGui.QColor(100, 200, 150)


class DotFInputPort(FlowInputPort):
    def setLabelVisible(self, visible):
        super(DotFInputPort, self).setLabelVisible(False)


class DotFOutputPort(FlowOutputPort):
    def setLabelVisible(self, visible):
        super(DotFOutputPort, self).setLabelVisible(False)


class DotPInputPort(ParameterInputPort):
    def setLabelVisible(self, visible):
        super(DotPInputPort, self).setLabelVisible(False)


class DotPOutputPort(ParameterOutputPort):
    def setLabelVisible(self, visible):
        super(DotPOutputPort, self).setLabelVisible(False)

