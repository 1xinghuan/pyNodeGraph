from .nodeItem import NodeItem
from pyNodeGraph.ui.graph.const import PORT_SPACING
from pyNodeGraph.module.sqt import QtGui


class PyNodeItem(NodeItem):
    nodeItemType = 'PyNodeItem'

    def addFlowPorts(self, flowPorts):
        for d in flowPorts:
            if d['type'] == 'input':
                self.addFlowInputPort(d['name'])
            elif d['type'] == 'output':
                self.addFlowOutputPort(d['name'])
            else:
                continue

    def setHighlight(self, value=True):
        super(PyNodeItem, self).setHighlight(value)
        if self.nodeObject.hasError:
            self.fillColor = QtGui.QColor(250, 0, 0)


class ForNodeItem(PyNodeItem):
    nodeItemType = 'ForNodeItem'

    def __init__(self, *args, **kwargs):
        super(ForNodeItem, self).__init__(*args, **kwargs)

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


NodeItem.registerNodeItem(PyNodeItem)
NodeItem.registerNodeItem(ForNodeItem)

