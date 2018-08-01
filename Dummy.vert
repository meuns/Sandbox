#version 450

layout(location=0) in vec4 AttributePosition;
layout(location=2) in vec3 AttributeColor;

out vec3 InterpColor;

void main()
{
    InterpColor = AttributeColor;
    gl_Position = AttributePosition;
}
