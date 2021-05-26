# -*- coding: utf-8 -*-

import json
from pyNodeGraph.module.sqt import *
from pyNodeGraph.ui.graph.const import *
from pyNodeGraph.core.parameter import (
    Parameter, StringParameter, TextParameter, FloatParameter, BoolParameter, Color4fParameter, IntParameter
)
from pyNodeGraph.utils.log import get_logger
from pyNodeGraph.utils.const import INPUT_ATTRIBUTE_PREFIX, OUTPUT_ATTRIBUTE_PREFIX
from pyNodeGraph.core.state.core import GraphState

logger = get_logger('pyNodeGraph.node')


class NodeTypes(object):
    def __init__(self, nodeClass):
        self.nodeClass = nodeClass
        self.parentNodeClass = [n for n in nodeClass.__mro__ if hasattr(n, 'nodeType')]
        self.parentNodeTypes = [n.nodeType for n in self.parentNodeClass]

    def isSubType(self, nodeType):
        return nodeType in self.parentNodeTypes


class Node(QtCore.QObject):
    parameterValueChanged = QtCore.Signal(object)
    parameterAdded = QtCore.Signal(object)
    parameterRemoved = QtCore.Signal(object)
    parameterPagesCleared = QtCore.Signal()

    _nodeTypes = {}

    nodeType = 'Node'
    nodeItemType = 'NodeItem'
    nodeGroup = 'Other'

    fillNormalColor = (50, 60, 70)
    fillHighlightColor = (230, 230, 100)
    borderNormalColor = (50, 60, 70)
    borderHighlightColor = (180, 180, 250)

    _expressionMap = {}

    @classmethod
    def convertColorToFloat(cls, color):
        return [i / 255.0 for i in color]

    @classmethod
    def convertColorTo255(cls, color):
        return [max(min(i * 255.0, 255.0), 0) for i in color]

    @classmethod
    def registerExpressionString(cls, string, object):
        cls._expressionMap[string] = object

    @classmethod
    def registerNode(cls, nodeObjectClass):
        nodeType = nodeObjectClass.nodeType
        cls._nodeTypes[nodeType] = nodeObjectClass
        nodeObjectClass.parameterDefaults = {}

    @classmethod
    def setParamDefault(cls, nodeType, paramName, value):
        nodeClass = cls._nodeTypes.get(nodeType)
        if nodeClass is not None:
            nodeClass.setParameterDefault(paramName, value)

    @classmethod
    def getAllNodeClassNames(cls):
        return list(cls._nodeTypes.keys())

    @classmethod
    def getAllNodeClass(cls):
        return list(cls._nodeTypes.values())

    @classmethod
    def setParameterDefault(cls, parameterName, value):
        cls.parameterDefaults.update({parameterName: value})

    @classmethod
    def getNodeClass(cls, nodeType):
        return cls._nodeTypes.get(nodeType, cls)

    @classmethod
    def getNodesByGroup(cls):
        result = {}
        for k, v in cls._nodeTypes.items():
            if v.nodeGroup not in result:
                result[v.nodeGroup] = []
            result[v.nodeGroup].append(v)
        return result

    @classmethod
    def Class(cls):
        return cls.nodeType

    @classmethod
    def NodeTypes(cls):
        return NodeTypes(cls)

    def __init__(self, item=None, name=''):
        super(Node, self).__init__()

        self.item = item
        self._name = name
        self._parameters = {}
        self._parametersName = []
        self._updateToDated = False
        self._metadata = {}
        self._defaultMetadata = {}

        self._beforeInitParameters()
        self._initParameters()
        self._initDefaults()
        self._setTags()

    def _beforeInitParameters(self):
        pass

    def _initParameters(self):
        self._parameters = {
            'name': StringParameter(name='name', default=self._name, parent=self, builtIn=True, hints={'tab': 'None'}),
            'label': TextParameter(name='label', default='', parent=self, builtIn=True, hints={'tab': 'Node'}),
            'labelFontSize': IntParameter(name='labelFontSize', default=10, parent=self, builtIn=True, hints={'tab': 'Node'}),
            'x': FloatParameter(name='x', default=None, parent=self, builtIn=True, visible=False, hints={'tab': 'Node'}),
            'y': FloatParameter(name='y', default=None, parent=self, builtIn=True, visible=False, hints={'tab': 'Node'}),
            'locked': BoolParameter(name='locked', default=False, parent=self, builtIn=True, visible=False, hints={'tab': 'Node'}),
            'disable': BoolParameter(name='disable', default=0, parent=self, builtIn=True, hints={'tab': 'Node'}),
            'fillColor': Color4fParameter(name='fillColor', parent=self, builtIn=True, hints={'showEditor': 'False', 'tab': 'None'}, default=self.convertColorToFloat(self.fillNormalColor)),
            'borderColor': Color4fParameter(name='borderColor', parent=self, builtIn=True, hints={'showEditor': 'False', 'tab': 'None'}, default=self.convertColorToFloat(self.borderNormalColor)),
        }
        self._parametersName = list(self._parameters.keys())
        self._parametersName.sort()

    def _initDefaults(self):
        for name in self.parameterDefaults.keys():
            defaultValue = self.parameterDefaults.get(name)
            self.parameter(name).setValueQuietly(defaultValue, override=False)
            self.parameter(name).setInheritValue(defaultValue)

    def _setTags(self):
        pass

    def parameter(self, parameterName):
        return self._parameters.get(parameterName)

    def hasParameter(self, name):
        return name in self._parameters

    def parameters(self):
        return [self._parameters.get(n) for n in self._parametersName]

    def name(self):
        return self.parameter('name').getValue()

    def hasProperty(self, name):
        if name in ['x', 'y']:
            return True
        return False

    def getProperty(self, name):
        if name == 'x':
            return self.item.scenePos().x()
        if name == 'y':
            return self.item.scenePos().y()

    def setProperty(self, name, value):
        if name == 'x':
            self.item.setX(value)
        elif name == 'y':
            self.item.setY(value)

    def _paramterValueChanged(self, parameter):
        logger.debug('{}, {}'.format(parameter.name(), parameter.getValue()))
        self.parameterValueChanged.emit(parameter)
        self._whenParamterValueChanged(parameter)
        GraphState.executeCallbacks(
            'parameterValueChanged',
            node=self, parameter=parameter
        )

    def _whenParamterValueChanged(self, parameter):
        if parameter.name() == 'name':
            self.item.scene()._afterNodeNameChanged(self.item)

    def addParameter(self, parameterName, parameterType, default=None, **kwargs):
        """
        :param parameterName:
        :param parameterType:
        :param default:
        :param custom:
        :return:
        """

        if self.hasParameter(parameterName):
            return self.parameter(parameterName)

        parameterClass = Parameter.getParameter(parameterType)
        if parameterClass is None:
            from pyNodeGraph.ui.utils.log import LogWindow
            message = 'Un-Support Parameter Type in addParameter! {}: {}'.format(parameterName, parameterType)
            LogWindow.warning(message)
            logger.warning(message)
            return

        label = kwargs.get('label', '')

        if label == '':
            label = parameterName
            order = None
            if parameterName.startswith(INPUT_ATTRIBUTE_PREFIX):
                label = parameterName.replace(INPUT_ATTRIBUTE_PREFIX, '')
            if parameterName.startswith(OUTPUT_ATTRIBUTE_PREFIX):
                label = parameterName.replace(OUTPUT_ATTRIBUTE_PREFIX, '')
            kwargs['label'] = label

        if parameterName.startswith(OUTPUT_ATTRIBUTE_PREFIX) and 'visible' not in kwargs:
            kwargs['visible'] = False

        parameter = parameterClass(
            parameterName,
            parent=self,
            default=default,
            **kwargs
        )
        self._parameters.update({parameterName: parameter})
        self._parametersName.append(parameterName)

        self.parameterAdded.emit(parameter)

        if parameterName.startswith(INPUT_ATTRIBUTE_PREFIX):
            self.item.addParameterInputPort(
                parameterName, label=label,
                dataType=parameter.__class__
            )
        if parameterName.startswith(OUTPUT_ATTRIBUTE_PREFIX):
            self.item.addParameterOutputPort(
                parameterName, label=label,
                dataType=parameter.__class__
            )

        return parameter

    def removeParameter(self, parameterName):
        if parameterName in self._parameters:
            # parameter = self.parameter(parameterName)
            self._parameters.pop(parameterName)
            self._parametersName.remove(parameterName)
            self.parameterRemoved.emit(parameterName)

            self.item.removeParameterPort(parameterName)

    def clearPages(self):
        self.parameterPagesCleared.emit()

    def isNodeLocked(self):
        return self.parameter('locked').getValue()

    def hasMetadatas(self):
        return self._metadata != {}

    def hasMetadata(self, key):
        return key in self._metadata

    def setMetadata(self, key, value):
        self._metadata[key] = str(value)

    def getMetadataValue(self, key, default=None):
        strValue = self._metadata.get(key, default)
        try:
            value = eval(strValue)
        except:
            value = strValue
        return value

    def getMetadataKeys(self):
        return list(self._metadata.keys())

    def getMetadatas(self):
        return self._metadata

    def getDefaultMetadatas(self):
        return self._defaultMetadata

    def getMetadatasAsString(self):
        return json.dumps(self._metadata, indent=4)

    def getActions(self):
        actions = [
        ]
        return actions


class DotNode(Node):
    nodeType = 'Dot'
    nodeItemType = 'DotItem'


class FlowDotNode(DotNode):
    nodeType = 'DotF'
    nodeItemType = 'FlowDotItem'


class ParamDotNode(DotNode):
    nodeType = 'DotP'
    nodeItemType = 'ParameterDotItem'


class BackdropNode(Node):
    nodeType = 'Backdrop'
    nodeItemType = 'BackdropItem'
    fillNormalColor = (50, 60, 70, 100)
    borderNormalColor = (50, 60, 70, 100)

    @classmethod
    def convertColorTo255(cls, color):
        color = super(BackdropNode, cls).convertColorTo255(color)
        if len(color) == 4:
            color[3] = 100
        return color

    def _initParameters(self):
        super(BackdropNode, self)._initParameters()

        self.addParameter('width', 'float', builtIn=True, visible=False, hints={'tab': 'Node'})
        self.addParameter('height', 'float', builtIn=True, visible=False, hints={'tab': 'Node'})

    def hasProperty(self, name):
        if name in ['width', 'height']:
            return True
        return super(BackdropNode, self).hasProperty(name)

    def getProperty(self, name):
        if name == 'width':
            return self.item.w
        if name == 'height':
            return self.item.h
        return super(BackdropNode, self).getProperty(name)

    def setProperty(self, name, value):
        super(BackdropNode, self).setProperty(name, value)
        if name == 'width':
            self.item.w = value
            self.item.setSizerPos()
        elif name == 'height':
            self.item.h = value
            self.item.setSizerPos()


import os
Node.registerExpressionString('os', os)

Node.registerNode(DotNode)
Node.registerNode(FlowDotNode)
Node.registerNode(ParamDotNode)
Node.registerNode(BackdropNode)

