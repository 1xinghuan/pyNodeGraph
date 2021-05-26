# -*- coding: utf-8 -*-

import copy
import json
from pyNodeGraph.module.sqt import QtCore


class Parameter(QtCore.QObject):
    parameterTypeString = '*'
    parameterWidgetString = None
    valueTypeName = None
    valueDefault = None

    fillNormalColor = (50, 100, 80)
    borderNormalColor = None

    valueChanged = QtCore.Signal(object)

    _parametersMap = {}
    _parameterWidgetsMap = {}

    @classmethod
    def registerParameter(cls, parameterClass):
        typeName = parameterClass.parameterTypeString
        cls._parametersMap.update({
            typeName: parameterClass
        })

    @classmethod
    def registerParameterWidget(cls, typeName, parameterWidget):
        cls._parameterWidgetsMap.update({
            typeName: parameterWidget
        })

    @classmethod
    def getParameterTypes(cls):
        return list(cls._parametersMap.keys())

    @classmethod
    def getParameter(cls, typeName):
        return cls._parametersMap.get(typeName)

    @classmethod
    def getValueDefault(cls):
        return cls.valueDefault

    @classmethod
    def convertValueFromPy(cls, pyValue):
        return cls._convertValueFromPy(pyValue)

    @classmethod
    def _convertValueFromPy(cls, pyValue):
        return pyValue

    @classmethod
    def convertValueToPy(cls, value):
        return cls._convertValueToPy(value)

    @classmethod
    def _convertValueToPy(cls, value):
        return value

    def __init__(
            self,
            name='',
            default=None,
            parent=None,
            builtIn=True,
            visible=True,
            label=None,
            custom=False,
            hints=None,
            **kwargs
    ):
        super(Parameter, self).__init__()

        self._name = name
        self._label = name if label is None else label
        self._node = parent

        default = default if default is not None else self.getValueDefault()

        self._defaultValue = default
        self._overrideValue = default
        self._overrideConnect = None

        self._valueOverride = False
        self._inheritValue = default
        self._inheritConnect = None

        self._metadata = {}
        self._defaultMetadata = {}

        self._hints = {} if hints is None else hints
        self.initHints(self._hints)
        self._defaultHints = self._hints.copy()

        self._builtIn = builtIn
        self._visible = visible
        self._isCustom = custom

        self._paramWidgets = []

        self._signalConnected = False
        self._reConnectSignal()

    def initHints(self, hints):
        widget = hints.get('widget', '')
        if widget == '':
            hints['widget'] = self.parameterWidgetString

    def addParamWidget(self, w):
        if w not in self._paramWidgets:
            self._paramWidgets.append(w)

    def removeParamWidget(self, w):
        self._paramWidgets.remove(w)

    def _breakSignal(self):
        if self._signalConnected:
            self._signalConnected = False
            self.valueChanged.disconnect(self._valueChanged)

    def _reConnectSignal(self):
        if not self._signalConnected:
            self._signalConnected = True
            self.valueChanged.connect(self._valueChanged)

    def _valueChanged(self, param):
        self._node._paramterValueChanged(param)

    def hasConnect(self):
        return self.getConnect() is not None

    def getDefaultValue(self):
        return self._defaultValue

    def name(self):
        return self._name

    def node(self):
        return self._node

    def nodeItem(self):
        return self._node.item

    def isBuiltIn(self):
        return self._builtIn

    def isVisible(self):
        return self._visible

    def setVisible(self, visible):
        self._visible = visible

    def getInheritValue(self):
        return self._inheritValue

    def getOverrideValue(self):
        return self._overrideValue

    def getValue(self):
        if self._node.hasProperty(self._name):
            return self._node.getProperty(self._name)
        if self.isOverride():
            return self.getOverrideValue()
        else:
            return self.getInheritValue()

    def getPyValue(self):
        v = self.getValue()
        return self.convertValueToPy(v)

    def getInheritConnect(self):
        return self._inheritConnect

    def getOverrideConnect(self):
        return self._overrideConnect

    def getConnect(self):
        return self._overrideConnect if self.isOverride() else self._inheritConnect

    def hasMetadatas(self):
        return self._metadata != {}

    def hasMetadata(self, key):
        return key in self._metadata

    def getMetadataKyes(self):
        return list(self._metadata.keys())

    def getMetadataValue(self, key, default=None):
        strValue = self._metadata.get(key, default)
        try:
            value = eval(strValue)
        except:
            value = strValue
        return value

    def getMetadatas(self):
        return self._metadata

    def getDefaultMetadatas(self):
        return self._defaultMetadata

    def getMetadatasAsString(self):
        return json.dumps(self._metadata, indent=4)

    def hasHint(self, key):
        return key in self._hints

    def getHints(self):
        return self._hints

    def getDefaultHints(self):
        return self._defaultHints

    def getHintValue(self, key, defaultValue=None, tryEval=True):
        value = self._hints.get(key, defaultValue)
        if tryEval:
            try:
                value = eval(value)
            except:
                value = value
        return value

    def getParameterWidgetClass(self):
        typeName = self.getHintValue('widget', tryEval=False)
        widgetClass = self._parameterWidgetsMap.get(typeName)
        return widgetClass

    # def getFlowValue(self):
    #     if self.hasConnect():
    #         connect = self.getConnect()
    #         nodeName = connect.split('.')[0]
    #         paramName = connect.split('.')[1]
    #         node = self.node().item.scene().getNode(nodeName)
    #         param = node.parameter(paramName)
    #         value = param.getValue()
    #     else:
    #         value = self.getValue()
    #     return value

    # --------------------set value--------------------
    def setMetadata(self, key, value):
        if key == 'custom' and value in [False, 'False']:
            return
        self._metadata[key] = str(value)

    def setHint(self, key, value):
        self._hints[key] = str(value)

    def _beforeSetValue(self):
        for w in self._paramWidgets:
            w._breakEditSignal()

    def _afterSetValue(self):
        for w in self._paramWidgets:
            w._reConnectEditSignal()

    def setValue(self, value, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._overrideValue = value
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setConnect(self, connect, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._overrideConnect = connect
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setInheritValue(self, value):
        self._inheritValue = value

    def setInheritConnect(self, connect):
        self._inheritConnect = connect

    def setValueQuietly(self, value, **kwargs):
        self.setValue(value, emitSignal=False, **kwargs)

    def setConnectQuietly(self, connect, **kwargs):
        self.setConnect(connect, emitSignal=False, **kwargs)

    def breakConnect(self):
        self._overrideConnect = None
        self.valueChanged.emit(self)

    def getShowValues(self):
        if self._valueOverride:
            return self.getValue(), self.getConnect()
        else:
            return self._inheritValue, self._inheritConnect

    def isCustom(self):
        if self._isCustom in [True, 'True', '1']:
            return True
        return False

    def setLabel(self, label):
        self._label = label

    def getLabel(self):
        return self._label

    def setOverride(self, override):
        self._valueOverride = override
        self.valueChanged.emit(self)

    def isOverride(self):
        return self._valueOverride

    def toXmlElement(self):
        from pyNodeGraph.core.parse._xml import ET

        custom = self.isCustom()
        builtIn = self.isBuiltIn()
        visible = self.isVisible()

        value = None
        connect = None

        if self.hasConnect():
            connect = self.getConnect()
        else:
            value = self.convertValueToPy(self.getValue())

        paramElement = ET.Element('p')
        paramElement.set('n', self.name())

        if not builtIn or custom:
            paramElement.set('t', self.parameterTypeString)
            if not visible:
                paramElement.set('vis', '0')
        if custom:
            paramElement.set('cus', str(custom))

        if connect is not None:
            paramElement.set('con', connect)
        else:
            v = str(value)
            if self.name() == 'label':
                v = v.replace('\n', '<\\n>')
            paramElement.set('val', v)

        for key, value in self.getMetadatas().items():
            if key in self.getDefaultMetadatas() and value == self.getDefaultMetadatas().get(key):
                continue
            metadataElement = ET.Element('m')
            metadataElement.set('k', key)
            metadataElement.set('v', value)
            paramElement.append(metadataElement)

        for key, value in self.getHints().items():
            if key in self.getDefaultHints() and value == self.getDefaultHints().get(key):
                continue
            hintElement = ET.Element('h')
            hintElement.set('k', str(key))
            hintElement.set('v', str(value))
            paramElement.append(hintElement)

        return paramElement

    def toXml(self):
        from pyNodeGraph.core.parse._xml import convertToString

        element = self.toXmlElement()
        return convertToString(element)

