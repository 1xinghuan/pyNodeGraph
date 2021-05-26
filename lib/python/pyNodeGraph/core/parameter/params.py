from .basic import Parameter


class ObjectParameter(Parameter):
    parameterTypeString = 'object'
    parameterWidgetString = 'str'
    valueDefault = None


class _StringParameter(ObjectParameter):
    fillNormalColor = (100, 130, 90)
    parameterWidgetString = 'str'
    valueDefault = ''


class StringParameter(_StringParameter):
    parameterTypeString = 'str'


class FilePathParameter(StringParameter):
    parameterTypeString = 'file'


class TextParameter(StringParameter):
    parameterTypeString = 'text'
    parameterWidgetString = 'text'


class ChooseParameter(StringParameter):
    parameterTypeString = 'choose'
    parameterWidgetString = 'choose'

    def addOptions(self, items):
        all = self.getOptions()
        all.extend(items)
        self.setHint('options', all)

    def getOptions(self):
        return self.getHintValue('options', defaultValue=[])


class _NonStringParameter(ObjectParameter):
    @classmethod
    def _convertValueFromPy(cls, pyValue):
        if isinstance(pyValue, str):
            pyValue = eval(pyValue)
        return pyValue


class _NonBuiltinParameter(ObjectParameter):
    @classmethod
    def _convertValueFromPy(cls, pyValue):
        return cls.valueDefault


class BoolParameter(_NonStringParameter):
    fillNormalColor = (180, 120, 50)
    parameterTypeString = 'bool'
    parameterWidgetString = 'boolean'
    valueDefault = False


class NumberParameter(_NonStringParameter):
    fillNormalColor = (75, 135, 185)
    parameterTypeString = 'number'
    parameterWidgetString = 'floating'
    valueDefault = 0


class IntParameter(NumberParameter):
    parameterTypeString = 'int'
    parameterWidgetString = 'integer'


class FloatParameter(NumberParameter):
    parameterTypeString = 'float'
    parameterWidgetString = 'floating'


class _VecParamter(_NonStringParameter):

    @classmethod
    def getValueDefault(cls):
        return []

    @classmethod
    def _convertValueToPy(cls, value):
        if value is not None:
            return [i for i in value]

    @classmethod
    def _convertValueFromPy(cls, pyValue):
        pyValue = super(_VecParamter, cls)._convertValueFromPy(pyValue)
        if pyValue is not None:
            return list(pyValue)


class Vec2fParameter(_VecParamter):
    parameterTypeString = 'float2'
    parameterWidgetString = 'vec2f'


class Vec3fParameter(_VecParamter):
    parameterTypeString = 'float3'
    parameterWidgetString = 'vec3f'


class Vec4fParameter(_VecParamter):
    parameterTypeString = 'float4'
    parameterWidgetString = 'vec4f'


class Color3fParameter(_VecParamter):
    parameterTypeString = 'color3f'
    parameterWidgetString = 'color3f'


class Color4fParameter(_VecParamter):
    parameterTypeString = 'color4f'
    parameterWidgetString = 'color4f'


# --------------------------------------- array ----------------------------------
class _ArrayParameter(_NonStringParameter):
    fillNormalColor = (220, 220, 20)
    valueDefault = []

    @classmethod
    def getChildParamType(cls):
        return cls.parameterTypeString.replace('[]', '')

    @classmethod
    def getChildParamClass(cls):
        paramClass = Parameter.getParameter(cls.getChildParamType())
        return paramClass

    @classmethod
    def _convertValueToPy(cls, value):
        childParamClass = cls.getChildParamClass()
        return [childParamClass.convertValueToPy(i) for i in value]

    @classmethod
    def _convertValueFromPy(cls, pyValue):
        pyValue = super(_ArrayParameter, cls)._convertValueFromPy(pyValue)
        if pyValue is None:
            return []
        childParamClass = cls.getChildParamClass()
        return list([childParamClass.convertValueFromPy(i) for i in pyValue])


class ObjectArrayParameter(_ArrayParameter):
    parameterTypeString = 'object[]'
    parameterWidgetString = 'object[]'


class StringArrayParameter(ObjectArrayParameter):
    parameterTypeString = 'str[]'
    parameterWidgetString = 'str[]'


class NumberArrayParameter(ObjectArrayParameter):
    parameterTypeString = 'number[]'
    parameterWidgetString = 'float[]'


class IntArrayParameter(NumberArrayParameter):
    parameterTypeString = 'int[]'
    parameterWidgetString = 'int[]'


class TokenArrayParameter(ObjectArrayParameter):
    parameterTypeString = 'token[]'
    parameterWidgetString = 'token[]'


class FloatArrayParameter(NumberArrayParameter):
    parameterTypeString = 'float[]'
    parameterWidgetString = 'float[]'


class Vec2fArrayParameter(ObjectArrayParameter):
    parameterTypeString = 'float2[]'
    parameterWidgetString = 'vec2f[]'


class Vec3fArrayParameter(ObjectArrayParameter):
    parameterTypeString = 'float3[]'
    parameterWidgetString = 'vec3f[]'


class Vec4fArrayParameter(ObjectArrayParameter):
    parameterTypeString = 'float4[]'
    parameterWidgetString = 'vec4f[]'


class Color3fArrayParameter(ObjectArrayParameter):
    parameterTypeString = 'color3f[]'
    parameterWidgetString = 'vec3f[]'

