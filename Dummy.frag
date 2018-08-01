#version 450

in vec3 InterpColor;

out vec4 FragmentColor;

void main()
{
    FragmentColor = vec4(InterpColor, 1.0);
}
