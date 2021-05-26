from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node


class _ListNode(PyFlowNode):
    nodeGroup = 'List'


class ListAppendNode(_ListNode):
    nodeType = 'List Append'
    args = [
        {'type': 'object[]', 'name': 'array', 'visible': False},
        {'type': 'object', 'name': 'add'},
    ]
    # results = [{'type': 'object[]'}]

    def _execute(self):
        l = self.getFlowValue('inputs:array')
        l.append(self.getFlowValue('inputs:add'))
        self.gotoNext()


class ListExtendNode(_ListNode):
    nodeType = 'List Extend'
    args = [
        {'type': 'object[]', 'name': 'array', 'visible': False},
        {'type': 'object[]', 'name': 'add', 'visible': False},
    ]
    # results = [{'type': 'object[]'}]

    def _execute(self):
        l = self.getFlowValue('inputs:array')
        l.extend(self.getFlowValue('inputs:add'))
        self.gotoNext()


class ListInsertNode(_ListNode):
    nodeType = 'List Insert'
    args = [
        {'type': 'object[]', 'name': 'array', 'visible': False},
        {'type': 'object', 'name': 'obj', 'visible': False},
        {'type': 'int', 'name': 'index'},
    ]
    # results = [{'type': 'object[]'}]

    def _execute(self):
        l = self.getFlowValue('inputs:array')
        l.insert(self.getFlowValue('inputs:index'), self.getFlowValue('inputs:obj'))
        self.gotoNext()


class ListRemoveNode(_ListNode):
    nodeType = 'List Remove'
    args = [
        {'type': 'object[]', 'name': 'array', 'visible': False},
        {'type': 'object', 'name': 'obj', 'visible': False},
    ]
    # results = [{'type': 'object[]'}]

    def _execute(self):
        l = self.getFlowValue('inputs:array')
        l.remove(self.getFlowValue('inputs:obj'))
        self.gotoNext()


Node.registerNode(ListAppendNode)
Node.registerNode(ListExtendNode)
Node.registerNode(ListInsertNode)
Node.registerNode(ListRemoveNode)

