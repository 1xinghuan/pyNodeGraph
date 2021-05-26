# -*- coding: utf-8 -*-

from .node import Node, DotNode


class PyNode(Node):
    nodeType = 'PyNode'
    nodeItemType = 'PyNodeItem'
    args = None
    results = None

    @classmethod
    def getArgsDefine(cls):
        if cls.args is not None:
            return cls.args
        return []

    @classmethod
    def getResultsDefine(cls):
        if cls.results is not None:
            return cls.results
        return []

    @classmethod
    def getParamsDefine(cls):
        return cls.getArgsDefine(), cls.getResultsDefine()

    def __init__(self, *args, **kwargs):
        super(PyNode, self).__init__(*args, **kwargs)
        self.hasError = False

    def _addParamsFromList(self, l, defaultName='name', namePrefix=''):
        for index, d in enumerate(l):
            name = d.get('name')
            if name is None:
                if len(l) == 1:
                    name = defaultName
                else:
                    name = '{0}{1}'.format(defaultName, index + 1)
            paramName = namePrefix + ':' + name
            options = {}
            if 'default' in d:
                options['default'] = d.get('default')
            if 'visible' in d:
                options['visible'] = d.get('visible')
            if 'hints' in d:
                options['hints'] = d.get('hints')
            self.addParameter(paramName, d.get('type'), **options)

    def _initParameters(self):
        super(PyNode, self)._initParameters()
        args, results = self.getParamsDefine()
        self._addParamsFromList(args, defaultName='arg', namePrefix='inputs')
        self._addParamsFromList(results, defaultName='result', namePrefix='outputs')

    def _getArgParams(self):
        return [i for i in self.parameters() if i.name().startswith('inputs:')]

    def _getResultParams(self):
        return [i for i in self.parameters() if i.name().startswith('outputs:')]

    def _beforeInitParameters(self):
        self.item.addFlowPorts(self.flowPorts)

    def _findUpNode(self, dot):
        upPort = dot.item.inputPort.getConnections()[0]
        upNode = upPort.node().nodeObject
        if isinstance(upNode, DotNode):
            upNode, name = self._findUpNode(upNode)
            return upNode, name
        else:
            return upNode, upPort.name

    def getFlowValue(self, paramName):
        param = self.parameter(paramName)
        if param.hasConnect():
            connect = param.getConnect()
            nodeName = connect.split('.')[0]
            paramName = connect.split('.')[1]

            upNode = self.item.scene().getNode(nodeName).nodeObject
            if isinstance(upNode, DotNode):
                upNode, paramName = self._findUpNode(upNode)
            if isinstance(upNode, PyNonFlowNode):
                upNode.execute()

            upParam = upNode.parameter(paramName)
            value = upParam.getValue()
        else:
            value = param.getValue()
        return value

    def execute(self):
        self._beforeExecute()
        self._execute()
        self._afterExecute()

    def _beforeExecute(self):
        self.hasError = False

    def _afterExecute(self):
        pass

    def _executeArgs(self, *args, **kwargs):
        return

    def _execute(self):
        params = self._getArgParams()
        args = []
        kwargs = {}
        for i in params:
            if i.name().startswith('inputs:arg'):
                args.append(self.getFlowValue(i.name()))
            else:
                kwargs.update({
                    i.name().replace('inputs:', ''): self.getFlowValue(i.name())
                })

        try:
            results = self._executeArgs(*args, **kwargs)
        except:
            self.emitError()
            raise
        for index, resultParam in enumerate(self._getResultParams()):
            resultParam.setValue(results[index])

    def emitError(self):
        self.hasError = True
        self.item.update()


class PyNonFlowNode(PyNode):
    fillNormalColor = (60, 50, 80)
    borderNormalColor = (140, 200, 190)
    flowPorts = []


class PyFlowNode(PyNode):
    flowPorts = [
        {'type': 'input', 'name': 'In'},
        {'type': 'output', 'name': 'Out'},
    ]

    def _findDotOutputNodes(self, dot, nodes=[]):
        port = dot.item.outputPort
        for nextPort in port.getConnections():
            node = nextPort.node().nodeObject
            if isinstance(node, DotNode):
                self._findDotOutputNodes(node, nodes)
            else:
                nodes.append(node)

    def gotoNext(self, name=None):
        if name is None:
            name = 'Out'
        port = self.item.getOutputPort(name)
        nextNodes = []

        for nextPort in port.getConnections():
            node = nextPort.node().nodeObject
            if isinstance(node, DotNode):
                self._findDotOutputNodes(node, nextNodes)
            else:
                nextNodes.append(node)

        for node in nextNodes:
            node.execute()


# class FlowNode(PyFlowNode):
#     flowPorts = [
#         {'type': 'input', 'name': 'In1'},
#         {'type': 'output', 'name': 'Out'},
#     ]
#     def getActions(self):
#         action = ['add_input', 'Add Input', None, self._addInputTriggered]
#         return [action]
#
#     def _addInputTriggered(self):
#         inparams = [p for p in self.parameters() if p.name().startswith('In')]
#         self.addParameter('In' + str(len(inparams) + 1), , custom=True)


class VarNode(PyNonFlowNode):
    fillNormalColor = (30, 85, 50)
    borderNormalColor = (220, 200, 250)
    varType = 'object'
    nodeGroup = 'Var'

    @classmethod
    def getResultsDefine(cls):
        return [
            {'type': cls.varType, 'visible': True}
        ]

    def _execute(self):
        pass


class VarObjectNode(VarNode):
    varType = 'object'
    nodeType = 'Var Object'


class VarStringNode(VarNode):
    varType = 'str'
    nodeType = 'Var String'


class VarTextNode(VarNode):
    varType = 'text'
    nodeType = 'Var Text'


class VarIntNode(VarNode):
    varType = 'int'
    nodeType = 'Var Int'


class VarFloatNode(VarNode):
    varType = 'float'
    nodeType = 'Var Float'


class VarBoolNode(VarNode):
    varType = 'bool'
    nodeType = 'Var Bool'


class VarNoneNode(VarNode):
    varType = 'object'
    nodeType = 'Var None'


class _AddPortNode(object):
    argType = 'object'
    def getAddPortAction(self):
        action = ['add_input', 'Add Input', None, self._addInputTriggered]
        return action

    def _addInputTriggered(self):
        inparams = [p for p in self.parameters() if p.name().startswith('inputs:arg')]
        self.addParameter('inputs:arg' + str(len(inparams) + 1), self.argType, custom=True)

    def _getArgParams(self):
        inparams = [p.name() for p in self.parameters() if p.name().startswith('inputs:arg')]
        return inparams


class VarObjectArrayNode(PyFlowNode, _AddPortNode):
    fillNormalColor = (30, 85, 50)
    borderNormalColor = (220, 200, 250)
    varType = 'object[]'
    nodeType = 'Var Object Array'

    @classmethod
    def getResultsDefine(cls):
        return [
            {'type': cls.varType, 'visible': False}
        ]

    def getActions(self):
        actions = []
        actions.append(self.getAddPortAction())
        return actions

    def _execute(self):
        result = []
        inparams = self._getArgParams()
        for p in inparams:
            result.append(self.getFlowValue(p.name()))
        self.parameter('outputs:result').setValue(result)
        self.gotoNext()


class VarStringArrayNode(VarObjectArrayNode):
    argType = 'str'
    varType = 'str[]'
    nodeType = 'Var String Array'


class VarNumberArrayNode(VarObjectArrayNode):
    argType = 'number'
    varType = 'number[]'
    nodeType = 'Var Number Array'


class VarIntArrayNode(VarNumberArrayNode):
    argType = 'int'
    varType = 'int[]'
    nodeType = 'Var Int Array'


class VarFloatArrayNode(VarNumberArrayNode):
    argType = 'float'
    varType = 'float[]'
    nodeType = 'Var Float Array'


class _ConvertNode(PyNonFlowNode):
    fillNormalColor = (30, 85, 50)
    borderNormalColor = (220, 200, 250)
    varType = 'object'
    nodeGroup = 'Var'
    args = [{'type': 'object'}]

    @classmethod
    def getResultsDefine(cls):
        return [
            {'type': cls.varType}
        ]

    def _executeArgs(self, *args, **kwargs):
        return


class ConvertToStrNode(_ConvertNode):
    varType = 'str'
    nodeType = 'To Str'
    def _executeArgs(self, *args, **kwargs):
        return [str(args[0])]


class OperationNode(PyNonFlowNode, _AddPortNode):
    fillNormalColor = (120, 50, 90)
    borderNormalColor = (90, 200, 150, 200)
    argType = 'object'
    argVisible = False
    resultType = 'object'
    nodeGroup = 'Operation'

    @classmethod
    def getArgsDefine(cls):
        return [
            {'type': cls.argType, 'visible': cls.argVisible},
            {'type': cls.argType, 'visible': cls.argVisible},
        ]

    @classmethod
    def getResultsDefine(cls):
        return [
            {'type': cls.resultType},
        ]

    def getActions(self):
        actions = []
        actions.append(self.getAddPortAction())
        return actions

    def _executeArgs(self, *args, **kwargs):
        result = args[0]
        for i in args[1:]:
            result = self._operate(result, i)
        return [result]

    def _operate(self, arg1, arg2):
        return


class PlusNode(OperationNode):
    nodeType = 'Plus'

    def _operate(self, arg1, arg2):
        return arg1 + arg2


class PlusStringNode(PlusNode):
    nodeType = 'Plus String'
    argType = 'str'
    argVisible = True


class PlusNumberNode(PlusNode):
    nodeType = 'Plus Number'
    argType = 'number'
    argVisible = True


class MinusNode(OperationNode):
    nodeType = 'Minus'

    def _operate(self, arg1, arg2):
        return arg1 - arg2


class MultiplyNode(OperationNode):
    nodeType = 'Multiply'

    def _operate(self, arg1, arg2):
        return arg1 * arg2


class MultiplyNumberNode(MultiplyNode):
    nodeType = 'Multiply Number'
    argType = 'number'
    argVisible = True


class DivideNode(OperationNode):
    nodeType = 'Divide'

    def _operate(self, arg1, arg2):
        return arg1 / arg2


class DivideNumberNode(DivideNode):
    nodeType = 'Divide Number'
    argType = 'number'
    argVisible = True


class MaxNode(OperationNode):
    nodeType = 'Max'

    def _operate(self, arg1, arg2):
        return max(arg1, arg2)


class MinNode(OperationNode):
    nodeType = 'Min'

    def _operate(self, arg1, arg2):
        return min(arg1, arg2)


class SignOperationNode(OperationNode):
    resultType = 'bool'


class MoreThanNode(SignOperationNode):
    nodeType = 'More Than'

    def _operate(self, arg1, arg2):
        return arg1 > arg2


class MoreThanOrEqualNode(SignOperationNode):
    nodeType = 'More Than Or Equal'

    def _operate(self, arg1, arg2):
        return arg1 >= arg2


class LessThanNode(SignOperationNode):
    nodeType = 'Less Than'

    def _operate(self, arg1, arg2):
        return arg1 < arg2


class LessThanOrEqualNode(SignOperationNode):
    nodeType = 'Less Than Or Equal'

    def _operate(self, arg1, arg2):
        return arg1 <= arg2


class EqualNode(SignOperationNode):
    nodeType = 'Equal'

    def _operate(self, arg1, arg2):
        return arg1 == arg2


class EqualStringNode(EqualNode):
    nodeType = 'Equal String'
    argType = 'str'
    argVisible = True


class IsNode(SignOperationNode):
    nodeType = 'Is'

    def _operate(self, arg1, arg2):
        return arg1 is arg2


class InNode(SignOperationNode):
    nodeType = 'In'

    def _operate(self, arg1, arg2):
        return arg1 in arg2


class InStringNode(InNode):
    nodeType = 'In String'
    argType = 'str'
    argVisible = True


class LogicOperationNode(OperationNode):
    argType = 'bool'
    resultType = 'bool'


class AndNode(LogicOperationNode):
    nodeType = 'And'

    def _operate(self, arg1, arg2):
        return arg1 and arg2


class OrNode(LogicOperationNode):
    nodeType = 'Or'

    def _operate(self, arg1, arg2):
        return arg1 or arg2


class _SingleArgLogicOperationNode(LogicOperationNode):
    @classmethod
    def getArgsDefine(cls):
        return [
            {'type': cls.argType, 'visible': False},
        ]

    @classmethod
    def getResultsDefine(cls):
        return [
            {'type': cls.resultType},
        ]


class NotNode(_SingleArgLogicOperationNode):
    nodeType = 'Not'
    argType = 'bool'
    resultType = 'bool'

    def _executeArgs(self, *args, **kwargs):
        return [not args[0]]


class IsNoneNode(_SingleArgLogicOperationNode):
    nodeType = 'Is None'
    argType = 'object'
    resultType = 'bool'

    def _executeArgs(self, *args, **kwargs):
        return [args[0] is None]


class IsNotNoneNode(_SingleArgLogicOperationNode):
    nodeType = 'Is Not None'
    argType = 'object'
    resultType = 'bool'

    def _executeArgs(self, *args, **kwargs):
        return [args[0] is not None]


class SumNode(PyNonFlowNode):
    nodeType = 'Sum'
    args = [{'type': 'number[]'}]
    results = [{'type': 'number'},]

    def _executeArgs(self, *args, **kwargs):
        return [sum(args[0])]


class RangeNode(PyNonFlowNode):
    nodeType = 'Range'
    args = [{'type': 'int'}]
    results = [{'type': 'int[]'},]

    def _executeArgs(self, *args, **kwargs):
        return [range(args[0])]


class LenNode(PyNonFlowNode):
    nodeType = 'Get Length'
    args = [{'type': 'object'}]
    results = [{'type': 'int'},]

    def _executeArgs(self, *args, **kwargs):
        return [len(args[0])]


class SliceNode(PyNonFlowNode):
    nodeType = 'Slice'
    args = [
        {'type': 'object', 'visible': False},
        {'type': 'int', 'name': 'start'},
        {'type': 'int', 'name': 'end'},
    ]
    results = [
        {'type': 'object'},
    ]

    def _executeArgs(self, *args, **kwargs):
        return [args[0][kwargs.get('start'):kwargs.get('end')]]


class SliceOneNode(PyNonFlowNode):
    nodeType = 'Slice One'
    args = [
        {'type': 'object', 'visible': False},
        {'type': 'int', 'name': 'index'},
    ]
    results = [
        {'type': 'object'},
    ]

    def _executeArgs(self, *args, **kwargs):
        return [args[0][kwargs.get('index')]]


class MainNode(PyFlowNode):
    nodeType = 'Main'
    fillNormalColor = (20, 10, 30)
    borderNormalColor = (240, 250, 240)
    flowPorts = [
        {'type': 'output', 'name': 'Out'},
    ]

    def _execute(self):
        self.gotoNext()


class PrintNode(PyFlowNode):
    nodeType = 'Print'
    fillNormalColor = (50, 60, 50)
    borderNormalColor = (200, 150, 150, 200)
    args = [
        {'type': 'object', 'visible': False},
    ]

    def _execute(self):
        value = self.getFlowValue('inputs:arg')
        print(value)
        self.gotoNext()


class LogicNode(PyFlowNode):
    fillNormalColor = (120, 10, 50)
    borderNormalColor = (90, 200, 150, 200)
    nodeGroup = 'Logic'


class ForNode(LogicNode):
    nodeType = 'For Loop'
    nodeItemType = 'ForNodeItem'
    flowPorts = [
        {'type': 'input', 'name': 'In'},
        {'type': 'output', 'name': 'For Each Loop'},
        {'type': 'output', 'name': 'Finally'},
    ]
    args = [
        {'name': 'array', 'type': 'object[]', 'visible': False},
    ]
    results = [
        {'name': 'index', 'type': 'int'},
        {'name': 'each', 'type': 'object'},
    ]

    def _execute(self):
        value = self.getFlowValue('inputs:array')
        for index, each in enumerate(value):
            self.parameter('outputs:index').setValue(index)
            self.parameter('outputs:each').setValue(each)
            self.gotoNext('For Each Loop')
        self.gotoNext('Finally')


class IfNode(LogicNode):
    nodeType = 'If'
    flowPorts = [
        {'type': 'input', 'name': 'In'},
        {'type': 'output', 'name': 'True'},
        {'type': 'output', 'name': 'False'},
    ]
    args = [
        {'type': 'bool', 'visible': False},
    ]

    def _execute(self):
        value = self.getFlowValue('inputs:arg')
        if value:
            self.gotoNext('True')
        else:
            self.gotoNext('False')


class TryNode(LogicNode):
    nodeType = 'Try'
    flowPorts = [
        {'type': 'input', 'name': 'In'},
        {'type': 'output', 'name': 'Try'},
        {'type': 'output', 'name': 'Execpt'},
        {'type': 'output', 'name': 'Finally'},
    ]

    def _execute(self):
        try:
            self.gotoNext('Try')
        except:
            self.gotoNext('Execpt')
        self.gotoNext('Finally')


class GetCurrentFileNode(PyNonFlowNode):
    nodeType = 'Get Current File'
    results = [{'type': 'str'}]

    def _executeArgs(self, *args, **kwargs):
        f = self.item.scene().path
        if f is None:
            f = ''
        return [f]


class GetCurrentDirNode(PyNonFlowNode):
    nodeType = 'Get Current Dir'
    results = [{'type': 'str'}]

    def _executeArgs(self, *args, **kwargs):
        import os
        f = self.item.scene().path
        if f is None:
            f = ''
        return [os.path.dirname(f)]


Node.registerNode(VarObjectNode)
Node.registerNode(VarStringNode)
Node.registerNode(VarTextNode)
Node.registerNode(VarIntNode)
Node.registerNode(VarFloatNode)
Node.registerNode(VarBoolNode)
Node.registerNode(VarObjectArrayNode)
Node.registerNode(VarStringArrayNode)
Node.registerNode(VarNumberArrayNode)
Node.registerNode(VarIntArrayNode)
Node.registerNode(VarFloatArrayNode)
Node.registerNode(ConvertToStrNode)

Node.registerNode(PlusNode)
Node.registerNode(PlusStringNode)
Node.registerNode(PlusNumberNode)
Node.registerNode(MinusNode)
Node.registerNode(MultiplyNode)
Node.registerNode(MultiplyNumberNode)
Node.registerNode(DivideNode)
Node.registerNode(DivideNumberNode)
Node.registerNode(MaxNode)
Node.registerNode(MinNode)
Node.registerNode(MoreThanNode)
Node.registerNode(MoreThanOrEqualNode)
Node.registerNode(LessThanNode)
Node.registerNode(LessThanOrEqualNode)
Node.registerNode(EqualNode)
Node.registerNode(EqualStringNode)
Node.registerNode(IsNode)
Node.registerNode(InNode)
Node.registerNode(InStringNode)

Node.registerNode(AndNode)
Node.registerNode(OrNode)
Node.registerNode(NotNode)
Node.registerNode(IsNoneNode)
Node.registerNode(IsNotNoneNode)

Node.registerNode(SumNode)
Node.registerNode(RangeNode)
Node.registerNode(LenNode)
Node.registerNode(SliceNode)
Node.registerNode(SliceOneNode)

Node.registerNode(MainNode)
Node.registerNode(PrintNode)
Node.registerNode(ForNode)
Node.registerNode(IfNode)
Node.registerNode(TryNode)

Node.registerNode(GetCurrentFileNode)
Node.registerNode(GetCurrentDirNode)

