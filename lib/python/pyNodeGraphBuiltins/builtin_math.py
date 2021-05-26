import math
from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node


class _MathNode(PyNonFlowNode):
    fillNormalColor = (80, 150, 70)
    borderNormalColor = (160, 180, 200)
    nodeGroup = 'Math'


class _SingleArgResultMathNode(_MathNode):
    args = [{'type': 'number'}]
    results = [{'type': 'number'}]


class _DoubleArgResultMathNode(_MathNode):
    args = [{'type': 'number'}, {'type': 'number'}]
    results = [{'type': 'number'}]


class GetCosNode(_SingleArgResultMathNode):
    nodeType = 'Get Cos'
    def _executeArgs(self, *args):
        return [math.cos(args[0])]


class GetSinNode(_SingleArgResultMathNode):
    nodeType = 'Get Sin'
    def _executeArgs(self, *args):
        return [math.sin(args[0])]


class GetTanNode(_SingleArgResultMathNode):
    nodeType = 'Get Tan'
    def _executeArgs(self, *args):
        return [math.tan(args[0])]


class GetACosNode(_SingleArgResultMathNode):
    nodeType = 'Get ACos'
    def _executeArgs(self, *args):
        return [math.acos(args[0])]


class GetASinNode(_SingleArgResultMathNode):
    nodeType = 'Get ASin'
    def _executeArgs(self, *args):
        return [math.asin(args[0])]


class GetATanNode(_SingleArgResultMathNode):
    nodeType = 'Get ATan'
    def _executeArgs(self, *args):
        return [math.atan(args[0])]


class GetCeilNode(_SingleArgResultMathNode):
    nodeType = 'Get Ceil'
    def _executeArgs(self, *args):
        return [math.ceil(args[0])]


class GetFloorNode(_SingleArgResultMathNode):
    nodeType = 'Get Floor'
    def _executeArgs(self, *args):
        return [math.floor(args[0])]


class GetFabsNode(_SingleArgResultMathNode):
    nodeType = 'Get Fabs'
    def _executeArgs(self, *args):
        return [math.fabs(args[0])]


class GetSqrtNode(_SingleArgResultMathNode):
    nodeType = 'Get Sqrt'
    def _executeArgs(self, *args):
        return [math.sqrt(args[0])]


class GetPowNode(_DoubleArgResultMathNode):
    nodeType = 'Get Pow'
    def _executeArgs(self, *args):
        return [math.pow(args[0], args[1])]


Node.registerNode(GetCosNode)
Node.registerNode(GetSinNode)
Node.registerNode(GetTanNode)
Node.registerNode(GetACosNode)
Node.registerNode(GetASinNode)
Node.registerNode(GetATanNode)
Node.registerNode(GetCeilNode)
Node.registerNode(GetFloorNode)
Node.registerNode(GetFabsNode)
Node.registerNode(GetSqrtNode)
Node.registerNode(GetPowNode)
