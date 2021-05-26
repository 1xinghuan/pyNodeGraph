import time
from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node


class _TimeNode(PyNonFlowNode):
    fillNormalColor = (80, 150, 70)
    borderNormalColor = (160, 180, 200)
    nodeGroup = 'Time'


class GetTimeNode(_TimeNode):
    nodeType = 'Get Time'
    results = [{'type': 'float'}]

    def _executeArgs(self, *args):
        return [time.time()]


Node.registerNode(GetTimeNode)

