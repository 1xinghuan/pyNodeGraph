import os

from pyNodeGraphBuiltins.plugin import *

pluginPaths = os.environ.get('PY_NODE_GRAPH_PLUGIN', '').split(os.pathsep)
for path in pluginPaths:
    if os.path.exists(path):
        pluginFile = os.path.join(path, 'plugin.py')
        if os.path.exists(pluginFile):
            with open(pluginFile, 'r') as f:
                string = f.read()
            exec(string)

