import os
from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node
from pyNodeGraph.ui.graph.nodeItem.pyNode import PyNodeItem
from pyNodeGraph.ui.graph.const import PORT_SPACING


class OsNode(PyNonFlowNode):
    fillNormalColor = (80, 150, 70)
    borderNormalColor = (160, 180, 200)
    nodeGroup = 'os'


class OsFlowNode(PyFlowNode):
    fillNormalColor = (80, 150, 70)
    borderNormalColor = (160, 180, 200)
    nodeGroup = 'os'


class GetJoinPathNode(OsNode):
    nodeType = 'Get Join Path'
    args = [{'type': 'str'}, {'type': 'str'}]
    results = [{'type': 'str'}]

    def _executeArgs(self, *args):
        return [os.path.join(*args)]


class SingleArgResultNode(OsNode):
    args = [{'type': 'str'}]
    results = [{'type': 'str'}]


class GetPathDirnameNode(SingleArgResultNode):
    nodeType = 'Get Path Dirname'

    def _executeArgs(self, *args):
        return [os.path.dirname(args[0])]


class GetPathBasenameNode(SingleArgResultNode):
    nodeType = 'Get Path Basename'

    def _executeArgs(self, *args):
        return [os.path.basename(args[0])]


class DoesPathExistsNode(OsNode):
    nodeType = 'Does Path Exists'
    args = [{'type': 'str'}]
    results = [{'type': 'bool'}]

    def _executeArgs(self, *args, **kwargs):
        return [os.path.exists(args[0])]


class GetDirContentNode(OsNode):
    nodeType = 'Get Dir Content'
    args = [{'type': 'str', 'name': 'dir'}]
    results = [{'type': 'str[]'}]

    def _executeArgs(self, *args, **kwargs):
        return [os.listdir(kwargs.get('dir'))]


class CreateFolderNode(OsFlowNode):
    nodeType = 'Create Folder'
    args = [
        {'type': 'str', 'name': 'path'},
    ]

    def _execute(self):
        path = self.getFlowValue('inputs:path')
        os.makedirs(path)
        self.gotoNext()


class RemoveFileNode(OsFlowNode):
    nodeType = 'Remove File'
    args = [
        {'type': 'str', 'name': 'path'},
    ]

    def _execute(self):
        path = self.getFlowValue('inputs:path')
        os.remove(path)
        self.gotoNext()


class RenameFileNode(OsFlowNode):
    nodeType = 'Rename File'
    args = [
        {'type': 'str', 'name': 'src'},
        {'type': 'str', 'name': 'dst'},
    ]

    def _execute(self):
        src = self.getFlowValue('inputs:src')
        dst = self.getFlowValue('inputs:dst')
        os.rename(src, dst)
        self.gotoNext()


class ExecuteCmdNode(OsFlowNode):
    nodeType = 'Execute CMD'
    args = [
        {'type': 'str', 'name': 'cmd'},
    ]

    def _execute(self):
        cmd = self.getFlowValue('inputs:cmd')
        os.system(cmd)
        self.gotoNext()


class OsWalkNode(OsFlowNode):
    nodeType = 'Walk Dir'
    nodeItemType = 'OsWalkNodeItem'
    args = [{'type': 'str', 'name': 'path'}]
    results = [
        {'name': 'root', 'type': 'str'},
        {'name': 'dir', 'type': 'str'},
        {'name': 'file', 'type': 'str'},
    ]
    flowPorts = [
        {'type': 'input', 'name': 'In'},
        {'type': 'output', 'name': 'For Each Root'},
        {'type': 'output', 'name': 'For Each Dir'},
        {'type': 'output', 'name': 'For Each File'},
        {'type': 'output', 'name': 'Finally'},
    ]

    def _execute(self):
        path = self.getFlowValue('inputs:path')
        for root, dirs, files in os.walk(path):
            self.parameter('outputs:root').setValue(root)
            self.gotoNext('For Each Root')
            for d in dirs:
                self.parameter('outputs:dir').setValue(d)
                self.gotoNext('For Each Dir')
            for f in files:
                self.parameter('outputs:file').setValue(f)
                self.gotoNext('For Each File')
        self.gotoNext('Finally')


class OsWalkNodeItem(PyNodeItem):
    nodeItemType = 'OsWalkNodeItem'

    def __init__(self, *args, **kwargs):
        super(OsWalkNodeItem, self).__init__(*args, **kwargs)

        bbox = self.boundingRect()

        for index, port in enumerate(self.outputParameterPorts):
            port.setPos(
                bbox.right() - port.w + port.w / 2.0,
                len(self.outputFlowPorts) * PORT_SPACING + index * PORT_SPACING
            )

        port = self.getPort('Finally')
        port.setPos(
            bbox.right() - port.w + port.w / 2.0,
            bbox.height() - 25
        )


PyNodeItem.registerNodeItem(OsWalkNodeItem)


Node.registerNode(GetJoinPathNode)
Node.registerNode(GetPathDirnameNode)
Node.registerNode(GetPathBasenameNode)
Node.registerNode(DoesPathExistsNode)
Node.registerNode(GetDirContentNode)
Node.registerNode(CreateFolderNode)
Node.registerNode(RemoveFileNode)
Node.registerNode(RenameFileNode)
Node.registerNode(ExecuteCmdNode)
Node.registerNode(OsWalkNode)

