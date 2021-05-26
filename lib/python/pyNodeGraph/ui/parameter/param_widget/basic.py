from pyNodeGraph.module.sqt import *
from pyNodeGraph.core.parameter import Parameter
from pyNodeGraph.utils.res import resource
from pyNodeGraph.core.state.core import GraphState
from pyNodeGraph.ui.utils.layout import clearLayout
from pyNodeGraph.utils.log import get_logger
from pyNodeGraph.ui.utils.log import LogWindow
from ..param_edit.number_edit import IntEditWidget, FloatEditWidget
from pyNodeGraph.utils.res import resource
from pyNodeGraph.ui.utils.layout import FormLayout

logger = get_logger('pyNodeGraph.ParameterWidget')


class ParameterWidget(object):
    # parameterClass = None
    editValueChanged = QtCore.Signal()

    @classmethod
    def createParameterWidget(cls, parameter):
        parameterWidgetClass = parameter.getParameterWidgetClass()

        if parameterWidgetClass is None:
            message = 'Un-Support Attribute Type in createParameterWidget! {}: {}: {}'.format(
                parameter.name(),
                parameter.parameterTypeString,
                parameter.getHintValue('widget', '')
            )
            LogWindow.warning(message)
            logger.warning(message)
            return

        parameterWidget = parameterWidgetClass()
        parameterWidget.setParameter(parameter)

        return parameterWidget

    def __init__(self):
        super(ParameterWidget, self).__init__()

        self._parameter = None
        self._signalBreaked = True
        self._editSignalBreaked = True

        self._connectEdit = None

        self._editSignalBreaked = False
        self.editValueChanged.connect(self._editWidgetValueChanged)

    def _editWidgetValueChanged(self):
        self._setValueFromEdit()

    def _breakEditSignal(self):
        if not self._editSignalBreaked:
            self._editSignalBreaked = True
            self.editValueChanged.disconnect(self._editWidgetValueChanged)

    def _reConnectEditSignal(self):
        if self._editSignalBreaked:
            self._editSignalBreaked = False
            self.editValueChanged.connect(self._editWidgetValueChanged)

    def _breakSignal(self):
        if not self._signalBreaked:
            self._signalBreaked = True
            self._parameter.valueChanged.disconnect(self._parameterValueChanged)
        # self._parameter._breakSignal()

    def _reConnectSignal(self):
        if self._signalBreaked:
            self._signalBreaked = False
            self._parameter.valueChanged.connect(self._parameterValueChanged)
        # self._parameter._reConnectSignal()

    def _parameterValueChanged(self, parameter):
        self.updateUI()

    def _setValueFromEdit(self):
        value = self.getPyValue()
        value = self._parameter.convertValueFromPy(value)

        self._breakSignal()
        self._parameter.setValue(value)
        self._reConnectSignal()

    def setParameter(self, parameter, update=False):
        self._parameter = parameter
        self._parameter.addParamWidget(self)
        self._reConnectSignal()
        if update:
            self.updateUI()

    def getParameter(self):
        return self._parameter

    def _setMasterWidgetEnable(self, enable):
        pass

    def _beforeUpdateUI(self):
        self._breakEditSignal()
        self._breakSignal()

    def _afterUpdateUI(self):
        self._reConnectEditSignal()
        self._reConnectSignal()

    def updateUI(self):
        self._beforeUpdateUI()
        self._updateUI()
        self._afterUpdateUI()

    def _updateUI(self):
        self.setToolTip(self._parameter.name())

        value, connect = self._parameter.getShowValues()
        hasConnect = connect is not None

        if hasConnect:
            if self._connectEdit is None:
                self._connectEdit = QtWidgets.QLineEdit()
                self._connectEdit.setStyleSheet('QLineEdit{background: rgb(60, 60, 70)}')
                self._connectEdit.setReadOnly(True)
                self.masterLayout.addWidget(self._connectEdit)

                # self._connectEdit.editingFinished.connect(self._connectEditChanged)

            self._connectEdit.setText(self._parameter.getConnect())

        self._setMasterWidgetEnable(not hasConnect)
        if self._connectEdit is not None:
            self._connectEdit.setVisible(hasConnect)

        value = self._parameter.convertValueToPy(value)
        self.setPyValue(value)

    def _connectEditChanged(self):
        self._breakSignal()
        connect = str(self._connectEdit.text())
        self._parameter.setConnect(connect)
        self._reConnectSignal()


class ArrayIndexLabel(QtWidgets.QLabel):
    removeClicked = QtCore.Signal(int)

    def __init__(self, index):
        super(ArrayIndexLabel, self).__init__()

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedWidth(20)
        self.setIndex(index)
        self.removePixmap = None

    def setIndex(self, index):
        self.index = index
        self.setText(str(index))

    def enterEvent(self, QEvent):
        super(ArrayIndexLabel, self).enterEvent(QEvent)
        if self.removePixmap is None:
            self.removePixmap = resource.get_pixmap('btn', 'close.png', scale=self.width())
        self.setPixmap(self.removePixmap)

    def leaveEvent(self, QEvent):
        super(ArrayIndexLabel, self).leaveEvent(QEvent)
        self.setText(str(self.index))

    def mouseReleaseEvent(self, QMouseEvent):
        super(ArrayIndexLabel, self).mouseReleaseEvent(QMouseEvent)
        self.removeClicked.emit(self.index)


class ArrayParameterWidget(QtWidgets.QWidget, ParameterWidget):
    editValueChanged = QtCore.Signal()

    def __init__(self):
        super(ArrayParameterWidget, self).__init__()
        ParameterWidget.__init__(self)

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.masterLayout.setSpacing(0)
        self.setLayout(self.masterLayout)

        self.expandButton = QtWidgets.QPushButton('expand...')
        self.expandButton.setFixedHeight(20)
        self.expandButton.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        ))

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumHeight(100)
        self.scrollArea.setVisible(0)
        self.areaWidget = None
        self.areaLayout = None
        self.formLayout = None

        self.masterLayout.addWidget(self.expandButton)
        self.masterLayout.addWidget(self.scrollArea)

        self.indexLabels = []
        self.editWidgets = []
        self.lineEdits = []
        self.expanded = 0

        self.expandButton.clicked.connect(self._expandClicked)

    def _setMasterWidgetEnable(self, enable):
        self.expandButton.setVisible(enable)
        self.scrollArea.setVisible(enable)

    def _getEditWidgetClass(self):
        return None

    def _getChildParamterClass(self):
        return None

    def _initArea(self):
        self.addButton = QtWidgets.QPushButton()
        self.addButton.setIcon(resource.get_qicon('btn', 'add_white.png'))
        self.addButton.setFixedSize(20, 20)

        self.areaWidget = QtWidgets.QWidget()
        self.areaLayout = QtWidgets.QVBoxLayout()
        self.areaLayout.setAlignment(QtCore.Qt.AlignTop)
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.addButton)
        self.buttonLayout.setAlignment(QtCore.Qt.AlignRight)

        self.formLayout = FormLayout()
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignCenter)
        self.areaLayout.addLayout(self.formLayout)
        self.areaLayout.addLayout(self.buttonLayout)
        self.areaWidget.setLayout(self.areaLayout)
        self.scrollArea.setWidget(self.areaWidget)

        self.addButton.clicked.connect(self._addClicked)

    def _addClicked(self):
        index = len(self.editWidgets)
        self.addEditWidget(
            index,
            pyValue=self._parameter.getChildParamClass().getValueDefault()
        )

    def _expandClicked(self):
        self.expanded = 1 - self.expanded
        if self.areaWidget is None:
            self._initArea()
        self.scrollArea.setVisible(self.expanded)
        self.expandButton.setFixedHeight(7 if self.expanded else 20)
        self.updateUI()

    def addEditWidget(self, index, pyValue=None):
        editWidgetClass = self._getEditWidgetClass()
        editWidget = editWidgetClass()
        editWidget.parameterWidget = self
        indexLabel = ArrayIndexLabel(index)

        editWidget.setPyValue(pyValue)

        self.indexLabels.append(indexLabel)
        self.editWidgets.append(editWidget)

        editWidget.editValueChanged.connect(self._editValueChanged)
        indexLabel.removeClicked.connect(self._editRemoveClicked)

        self.formLayout.addRow(indexLabel, editWidget)

    def _updateUI(self):
        self.setToolTip(self._parameter.name())
        text = 'expand...{}'.format(len(self._parameter.getValue()))
        self.expandButton.setText(text)
        self.expandButton.setToolTip(text)

        if self.formLayout is not None and self.scrollArea.isVisible():
            clearLayout(self.formLayout)
            self.indexLabels = []
            self.editWidgets = []

            value = self._parameter.getValue()
            value = self._parameter.convertValueToPy(value)

            for index, v in enumerate(value):
                self.addEditWidget(index, pyValue=v)

    def _editValueChanged(self):
        value = [edit.getPyValue() for edit in self.editWidgets]
        value = self._parameter.convertValueFromPy(value)

        self._breakSignal()
        self._parameter.setValue(value)
        self._reConnectSignal()

    def _editRemoveClicked(self, index):
        indexLabel = self.indexLabels[index]
        editWidget = self.editWidgets[index]
        self.indexLabels.remove(indexLabel)
        self.editWidgets.remove(editWidget)

        self.formLayout.removeRowWidget(editWidget)

        for i in self.indexLabels:
            if i.index > index:
                i.setIndex(i.index - 1)


class BasicWidget(object):
    def __init__(self):
        super(BasicWidget, self).__init__()

        self._isNumber = True

    def setValue(self, value):
        pass


class BasicLineEdit(QtWidgets.QLineEdit, BasicWidget):
    def __init__(self):
        super(BasicLineEdit, self).__init__()
        BasicWidget.__init__(self)

        self._editWidget = None
        self._editMode = False
        self._editStartPos = None

    def setValue(self, value):
        self.setText(str(value))
        self.updateUI()

    def setText(self, string):
        super(BasicLineEdit, self).setText(string)
        self.setCursorPosition(0)

    def updateUI(self):
        self.setStyleSheet('QLineEdit{background: rgb(40, 40, 40)}')
        self.setReadOnly(False)

    def getRealValue(self):
        text = str(self.text())
        validator = self.validator()
        if validator is None:
            value = text
        elif isinstance(validator, QtGui.QIntValidator):
            try:  # may be ''
                value = int(text)
            except:
                value = 0
        else:
            try:  # may be ''
                value = float(text)
            except:
                value = 0
        return value

    def mousePressEvent(self, event):
        super(BasicLineEdit, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.MiddleButton:
            self._enableEditMode()
            self._editStartPos = QtGui.QCursor.pos()

    def mouseReleaseEvent(self, event):
        super(BasicLineEdit, self).mouseReleaseEvent(event)
        if event.button() == QtCore.Qt.MiddleButton:
            self._disableEditMode()

    def mouseMoveEvent(self, event):
        super(BasicLineEdit, self).mouseMoveEvent(event)
        if self._editMode:
            targetPos = QtGui.QCursor.pos()
            QtGui.QCursor.setPos(self._editStartPos.x(), targetPos.y())
            value = self._editWidget.setEditingPos(targetPos - self._editStartPos)
            currentValue = self.getRealValue()
            self.setText(str(currentValue + value))
            self.editingFinished.emit()

    def _enableEditMode(self):
        from pyNodeGraph.ui.nodeGraph import PY_NODE_GRAPH_WINDOW

        pos = PY_NODE_GRAPH_WINDOW.mapFromGlobal(QtGui.QCursor.pos())
        x = pos.x() - self._editWidget.width() / 2
        y = pos.y() - self._editWidget.height() / 2
        self._editWidget.move(x, y)
        self._editWidget.setVisible(True)

        self._editMode = True

    def _disableEditMode(self):
        self._editMode = False
        if self._editWidget is not None:
            self._editWidget.setVisible(False)


class IntLineEdit(BasicLineEdit):
    def __init__(self):
        super(IntLineEdit, self).__init__()

        validator = QtGui.QIntValidator()
        self.setValidator(validator)

    def _enableEditMode(self):
        if self._editWidget is None:
            from pyNodeGraph.ui.nodeGraph import PY_NODE_GRAPH_WINDOW
            self._editWidget = IntEditWidget(
                parent=PY_NODE_GRAPH_WINDOW
            )
            self._editWidget.show()
        super(IntLineEdit, self)._enableEditMode()


class FloatLineEdit(BasicLineEdit):
    def __init__(self):
        super(FloatLineEdit, self).__init__()

        validator = QtGui.QDoubleValidator()
        self.setValidator(validator)

    def _enableEditMode(self):
        if self._editWidget is None:
            from pyNodeGraph.ui.nodeGraph import PY_NODE_GRAPH_WINDOW
            self._editWidget = FloatEditWidget(
                parent=PY_NODE_GRAPH_WINDOW
            )
            self._editWidget.show()
        super(FloatLineEdit, self)._enableEditMode()


class VecWidget(QtWidgets.QWidget):
    editValueChanged = QtCore.Signal()
    _valueSize = 1
    _lineEdit = BasicLineEdit

    def __init__(self):
        super(VecWidget, self).__init__()

        self.initUI()

    def initUI(self):
        self.masterLayout = QtWidgets.QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.lineEdits = []
        for i in range(self._valueSize):
            lineEdit = self._lineEdit()

            # lineEdit.returnPressed.connect(self._editTextChanged)
            lineEdit.editingFinished.connect(self._editTextChanged)
            # lineEdit.textChanged.connect(self._editTextChanged)

            self.masterLayout.addWidget(lineEdit)
            self.lineEdits.append(lineEdit)

    def _editTextChanged(self):
        lineEdit = self.sender()
        self.editValueChanged.emit()

    def setEditorsVisible(self, visible):
        for i in self.lineEdits:
            i.setVisible(visible)

    def setPyValue(self, value):
        if not isinstance(value, list):
            value = [value]
        for index, v in enumerate(value):
            lineEdit = self.lineEdits[index]
            lineEdit.setValue(v)

    def getPyValue(self):
        value = []
        for edit in self.lineEdits:
            num = edit.getRealValue()
            value.append(num)

        if len(value) == 1:
            value = value[0]
        return value

    def updateLineEditsUI(self):
        for lineEdit in self.lineEdits:
            lineEdit.updateUI()


class MatrixWidget(VecWidget):
    _lineEdit = FloatLineEdit

    def initUI(self):
        self.masterLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.lineEdits = []
        for i in range(self._valueSize):
            layout = QtWidgets.QHBoxLayout()
            for j in range(self._valueSize):
                lineEdit = self._lineEdit()
                lineEdit.editingFinished.connect(self._editTextChanged)
                self.lineEdits.append(lineEdit)

                layout.addWidget(lineEdit)

            self.masterLayout.addLayout(layout)

    def setPyValue(self, value):
        if not isinstance(value, list):
            value = [value]
        for i, vec in enumerate(value):
            for j, v in enumerate(vec):
                index = i * self._valueSize + j
                lineEdit = self.lineEdits[index]
                lineEdit.setValue(v)

    def getPyValue(self):
        value = [[] for i in range(self._valueSize)]
        for index, edit in enumerate(self.lineEdits):
            i = index / self._valueSize
            j = index % self._valueSize

            num = edit.getRealValue()
            value[i].append(num)

        return value


class VecParameterWidget(ParameterWidget):
    def _setMasterWidgetEnable(self, enable):
        super(VecParameterWidget, self)._setMasterWidgetEnable(enable)
        self.setEditorsVisible(enable)

