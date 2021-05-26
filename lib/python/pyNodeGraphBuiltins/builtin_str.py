from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node


class _StrNode(PyNonFlowNode):
    nodeGroup = 'String'


# class _StrSingleArgResultNode(_StrNode):
#     args = [{'type': 'str'}]


class StartsWithNode(_StrNode):
    args = [{'type': 'str', 'name': 'string'}, {'type': 'str', 'name': 'prefix'}]
    results = [{'type': 'bool'}]
    nodeType = 'Starts With'

    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').startswith(kwargs.get('prefix'))]


class EndsWithNode(_StrNode):
    args = [{'type': 'str', 'name': 'string'}, {'type': 'str', 'name': 'suffix'}]
    results = [{'type': 'bool'}]
    nodeType = 'Ends With'

    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').endswith(kwargs.get('suffix'))]


class FindNode(_StrNode):
    args = [{'type': 'str', 'name': 'string'}, {'type': 'str', 'name': 'sub'}]
    results = [{'type': 'int'}]
    nodeType = 'Find String'

    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').find(kwargs.get('sub'))]


class StripNode(_StrNode):
    args = [{'type': 'str', 'name': 'string'}, {'type': 'str', 'name': 'sub'}]
    results = [{'type': 'str'}]
    nodeType = 'Strip String'

    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').strip(kwargs.get('sub'))]


class LStripNode(StripNode):
    nodeType = 'Strip String Left'
    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').lstrip(kwargs.get('sub'))]


class RStripNode(StripNode):
    nodeType = 'Strip String Right'
    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').rstrip(kwargs.get('sub'))]


class SplitNode(_StrNode):
    args = [{'type': 'str', 'name': 'string'}, {'type': 'str', 'name': 'split'}]
    results = [{'type': 'str[]'}]
    nodeType = 'Split'

    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').split(kwargs.get('split'))]


class ReplaceNode(_StrNode):
    args = [
        {'type': 'str', 'name': 'string'},
        {'type': 'str', 'name': 'from'},
        {'type': 'str', 'name': 'to'}
    ]
    results = [{'type': 'str'}]
    nodeType = 'Replace'

    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('string').replace(kwargs.get('from'), kwargs.get('to'))]


class JoinNode(_StrNode):
    args = [
        {'type': 'str', 'name': 'split'},
        {'type': 'str[]', 'name': 'array', 'visible': False},
    ]
    results = [{'type': 'str'}]
    nodeType = 'Join'

    def _executeArgs(self, *args, **kwargs):
        return [kwargs.get('split').join(kwargs.get('array'))]


class _SingleArgResultStrNode(_StrNode):
    args = [{'type': 'str'},]
    results = [{'type': 'str'}]


class CapitalizeNode(_SingleArgResultStrNode):
    nodeType = 'Capitalize String'

    def _executeArgs(self, *args, **kwargs):
        return [args[0].capitalize()]


class LowerNode(_SingleArgResultStrNode):
    nodeType = 'Lower String'

    def _executeArgs(self, *args, **kwargs):
        return [args[0].lower()]


class UpperNode(_SingleArgResultStrNode):
    nodeType = 'Upper String'

    def _executeArgs(self, *args, **kwargs):
        return [args[0].upper()]


class SwapcaseNode(_SingleArgResultStrNode):
    nodeType = 'Swapcase String'

    def _executeArgs(self, *args, **kwargs):
        return [args[0].swapcase()]


Node.registerNode(StartsWithNode)
Node.registerNode(EndsWithNode)
Node.registerNode(FindNode)
Node.registerNode(StripNode)
Node.registerNode(LStripNode)
Node.registerNode(RStripNode)

Node.registerNode(SplitNode)
Node.registerNode(ReplaceNode)
Node.registerNode(JoinNode)
Node.registerNode(CapitalizeNode)
Node.registerNode(LowerNode)
Node.registerNode(UpperNode)
Node.registerNode(SwapcaseNode)

