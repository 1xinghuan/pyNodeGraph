from pyNodeGraph.core.node.pyNode import PyNonFlowNode, PyFlowNode, Node
from pyNodeGraph.core.parameter.params import ObjectParameter, _NonBuiltinParameter


class FileFlowNode(PyFlowNode):
    fillNormalColor = (95, 95, 145)
    borderNormalColor = (170, 250, 160)
    nodeGroup = 'File'


class FileNonFlowNode(PyNonFlowNode):
    fillNormalColor = (95, 95, 145)
    borderNormalColor = (170, 250, 160)
    nodeGroup = 'File'


class OpenFileNode(FileFlowNode):
    nodeType = 'Open File'
    args = [
        {'type': 'str', 'name': 'file'},
        {
            'type': 'choose', 'name': 'mode',
            'hints': {
                'options': [
                    ['read', 'r'],
                    ['write', 'w'],
                    ['append', 'a']
                ]},
            'default': 'r'},
    ]
    results = [
        {'type': 'fileIO', 'name': 'result'},
    ]

    def _execute(self):
        file = self.getFlowValue('inputs:file')
        mode = self.getFlowValue('inputs:mode')
        f = open(file, mode)
        self.parameter('outputs:result').setValue(f)
        self.gotoNext()
        f.close()


class FileReadNode(FileNonFlowNode):
    nodeType = 'Read File'
    args = [{'type': 'fileIO', 'name': 'file'}]
    results = [{'type': 'object', 'name': 'result'}]

    def _executeArgs(self, *args, **kwargs):
        f = kwargs.get('file')
        return [f.read()]


class FileReadLinesNode(FileNonFlowNode):
    nodeType = 'Read Lines'
    args = [{'type': 'fileIO', 'name': 'file'}]
    results = [{'type': 'str[]', 'name': 'result'}]

    def _executeArgs(self, *args, **kwargs):
        f = kwargs.get('file')
        return [f.readlines()]


class FileWriteLinesNode(FileFlowNode):
    nodeType = 'Write Lines'
    args = [
        {'type': 'fileIO', 'name': 'file'},
        {'type': 'str[]', 'name': 'seq'},
    ]

    def _execute(self):
        f = self.getFlowValue('inputs:file')
        seq = self.getFlowValue('inputs:seq')
        f.writelines(seq)
        self.gotoNext()


class FileIOParameter(_NonBuiltinParameter):
    parameterTypeString = 'fileIO'


ObjectParameter.registerParameter(FileIOParameter)

Node.registerNode(OpenFileNode)
Node.registerNode(FileReadNode)
Node.registerNode(FileReadLinesNode)
Node.registerNode(FileWriteLinesNode)

