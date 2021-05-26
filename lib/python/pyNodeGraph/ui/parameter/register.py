from pyNodeGraph.core.parameter.basic import Parameter
from .param_widget import *


Parameter.registerParameter(ObjectParameter)
Parameter.registerParameter(StringParameter)
Parameter.registerParameter(ChooseParameter)
Parameter.registerParameter(FilePathParameter)
Parameter.registerParameter(TextParameter)
Parameter.registerParameter(BoolParameter)
Parameter.registerParameter(NumberParameter)
Parameter.registerParameter(IntParameter)
Parameter.registerParameter(FloatParameter)
Parameter.registerParameter(Vec2fParameter)
Parameter.registerParameter(Vec3fParameter)
Parameter.registerParameter(Vec4fParameter)
Parameter.registerParameter(Color3fParameter)
Parameter.registerParameter(Color4fParameter)

Parameter.registerParameter(ObjectArrayParameter)
Parameter.registerParameter(StringArrayParameter)
Parameter.registerParameter(TokenArrayParameter)
Parameter.registerParameter(NumberArrayParameter)
Parameter.registerParameter(IntArrayParameter)
Parameter.registerParameter(FloatArrayParameter)
Parameter.registerParameter(Vec2fArrayParameter)
Parameter.registerParameter(Vec3fArrayParameter)
Parameter.registerParameter(Vec4fArrayParameter)
Parameter.registerParameter(Color3fArrayParameter)


Parameter.registerParameterWidget('object', StringParameterWidget)
Parameter.registerParameterWidget('str', StringParameterWidget)
Parameter.registerParameterWidget('choose', ChooseParameterWidget)
Parameter.registerParameterWidget('text', TextParameterWidget)
Parameter.registerParameterWidget('boolean', BoolParameterWidget)
Parameter.registerParameterWidget('integer', IntParameterWidget)
Parameter.registerParameterWidget('floating', FloatParameterWidget)

Parameter.registerParameterWidget('vec2f', Vec2fParameterWidget)
Parameter.registerParameterWidget('vec3f', Vec3fParameterWidget)
Parameter.registerParameterWidget('vec4f', Vec4fParameterWidget)
Parameter.registerParameterWidget('color', Color3fParameterWidget)
Parameter.registerParameterWidget('color3f', Color3fParameterWidget)
Parameter.registerParameterWidget('color4f', Color4fParameterWidget)

Parameter.registerParameterWidget('object[]', StringArrayParameterWidget)
Parameter.registerParameterWidget('str[]', StringArrayParameterWidget)
Parameter.registerParameterWidget('int[]', IntArrayParameterWidget)
Parameter.registerParameterWidget('float[]', FloatArrayParameterWidget)
Parameter.registerParameterWidget('vec2f[]', Vec2fArrayParameterWidget)
Parameter.registerParameterWidget('vec3f[]', Vec3fArrayParameterWidget)
Parameter.registerParameterWidget('vec4f[]', Vec4fArrayParameterWidget)


