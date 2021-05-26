import sys
import getpass
import platform
from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node


class _SysNode(PyNonFlowNode):
    fillNormalColor = (80, 150, 70)
    borderNormalColor = (160, 180, 200)
    nodeGroup = 'System'


class GetUserNode(_SysNode):
    nodeType = 'Get User'
    results = [{'type': 'str'}]

    def _executeArgs(self, *args):
        return [getpass.getuser()]


class GetSystemPlatformNode(_SysNode):
    nodeType = 'Get System Platform'
    results = [{'type': 'str'}]

    def _executeArgs(self, *args):
        return [sys.platform]


class GetPlatformSystemNode(_SysNode):
    nodeType = 'Get Platform System'
    results = [{'type': 'str'}]

    def _executeArgs(self, *args):
        return [platform.system()]


class GetPlatformVersionNode(_SysNode):
    nodeType = 'Get Platform Version'
    results = [{'type': 'str'}]

    def _executeArgs(self, *args):
        return [platform.version()]


Node.registerNode(GetUserNode)
Node.registerNode(GetPlatformSystemNode)
Node.registerNode(GetPlatformVersionNode)
Node.registerNode(GetSystemPlatformNode)


