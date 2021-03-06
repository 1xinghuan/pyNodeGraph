from pyNodeGraph.core.parameter import *
from .widgets import *


class IntArrayParameterWidget(ArrayParameterWidget):
    def _getChildParamterClass(self):
        return IntParameter

    def _getEditWidgetClass(self):
        return IntWidget


class FloatArrayParameterWidget(ArrayParameterWidget):
    def _getChildParamterClass(self):
        return FloatParameter

    def _getEditWidgetClass(self):
        return FloatWidget


class Vec2fArrayParameterWidget(ArrayParameterWidget):
    def _getChildParamterClass(self):
        return Vec2fParameter

    def _getEditWidgetClass(self):
        return Vec2fWidget


class Vec3fArrayParameterWidget(ArrayParameterWidget):
    def _getChildParamterClass(self):
        return Vec3fParameter

    def _getEditWidgetClass(self):
        return Vec3fWidget


class Vec4fArrayParameterWidget(ArrayParameterWidget):
    def _getChildParamterClass(self):
        return Vec4fParameter

    def _getEditWidgetClass(self):
        return Vec4fWidget


class StringArrayParameterWidget(ArrayParameterWidget):
    def _getChildParamterClass(self):
        return StringParameter

    def _getEditWidgetClass(self):
        return VecWidget

