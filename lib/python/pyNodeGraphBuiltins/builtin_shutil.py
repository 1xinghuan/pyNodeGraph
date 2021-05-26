import shutil
from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node


class ShutilFlowNode(PyFlowNode):
    fillNormalColor = (65, 145, 75)
    borderNormalColor = (180, 220, 250)
    nodeGroup = 'shutil'


class CopyFileNode(ShutilFlowNode):
    nodeType = 'Copy File'
    args = [
        {'type': 'str', 'name': 'src'},
        {'type': 'str', 'name': 'dst'},
    ]

    def _execute(self):
        src = self.getFlowValue('inputs:src')
        dst = self.getFlowValue('inputs:dst')
        shutil.copyfile(src, dst)
        self.gotoNext()


class RemoveTreeNode(ShutilFlowNode):
    nodeType = 'Remove Tree'
    args = [
        {'type': 'str', 'name': 'src'},
    ]

    def _execute(self):
        src = self.getFlowValue('inputs:src')
        shutil.rmtree(src)
        self.gotoNext()


Node.registerNode(CopyFileNode)
Node.registerNode(RemoveTreeNode)


