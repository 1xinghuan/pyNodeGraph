from pyNodeGraph.module.sqt import QtCore


class GraphState(QtCore.QObject):

    _callbacks = {}
    _functions = {}

    _state = None

    @classmethod
    def addCallback(cls, callbackType, func):
        if callbackType not in cls._callbacks:
            cls._callbacks[callbackType] = []
        cls._callbacks[callbackType].append(func)

    @classmethod
    def clearAllCallbacks(cls):
        cls._callbacks = {}
    
    @classmethod
    def getAllCallbacks(cls):
        return cls._callbacks

    @classmethod
    def executeCallbacks(cls, callbackType, **kwargs):
        funcs = cls._callbacks.get(callbackType, [])
        kwargs.update({'type': callbackType})
        for func in funcs:
            func(**kwargs)

    @classmethod
    def setFunction(cls, funcName, func):
        cls._functions[funcName] = func

    @classmethod
    def hasFunction(cls, funcName):
        return funcName in cls._functions

    @classmethod
    def executeFunction(cls, funcName, *args, **kwargs):
        func = cls._functions.get(funcName)
        if func is not None:
            return func(*args, **kwargs)

