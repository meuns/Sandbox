# coding: utf8

from itertools import islice
from random import random

from OpenGL.GL import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_SHADER_STORAGE_BUFFER, GL_LINES, \
    glBindVertexArray, glUseProgram, glDrawArrays, glBindBufferBase

from Shader import initialize_shader, initialize_program, dispose_program
from Buffer import prepare_float_buffer_data, initialize_buffer, dispose_buffer
from Vertex import initialize_vertex_array, dispose_vertex_array


def prepare_lines(line_strip):

    lines = []
    for data0, data1 in zip(islice(line_strip, 0, len(line_strip) - 1), islice(line_strip, 1, None)):
        lines.append(data0)
        lines.append(data1)
    return lines


INTX_LINE_COUNT = 128
INTX_POINT_COUNT = INTX_LINE_COUNT + 1
#INT0_X = [-1.0 + (i / INTX_LINE_COUNT) * 2.0 for i in range(INTX_POINT_COUNT)]
#INT0_Y = [+.2] * INTX_POINT_COUNT
INT1_X = [-1.0 + (i / INTX_LINE_COUNT) * 2.0 for i in range(INTX_POINT_COUNT)]
INT1_Y = [-.2 + 0.01 * random() for i in range(INTX_POINT_COUNT)]
WORLD_LINE_COUNT = INTX_LINE_COUNT #* 2


BUFFER_LAYOUT = """
#define WORLD_LINE_COUNT %d

layout(std430, binding = 0) buffer World
{
    float world_px[WORLD_LINE_COUNT << 1];
    float world_py[WORLD_LINE_COUNT << 1];
};

void get_world_line(uint first_point_index, out vec2 p0, out vec2 p1)
{
    p0 = vec2(world_px[first_point_index + 0], world_py[first_point_index + 0]);
    p1 = vec2(world_px[first_point_index + 1], world_py[first_point_index + 1]);
}
""" % WORLD_LINE_COUNT


DISPLAY_NORMAL_VERTEX_SHADER = """
#version 430

{buffer_layout}

void main()
{{
    vec2 p0, p1;
    get_world_line((gl_VertexID >> 1) << 1, p0, p1);
    
    vec2 pc = (p0 + p1) * 0.5;
    
    if (gl_VertexID % 2 == 0)
    {{
        gl_Position = vec4(pc, 0.0, 1.0);
    }}
    else
    {{
        gl_Position = vec4(pc + (p1 - p0).yx * vec2(-1.0, 1.0) * 0.25, 0.0, 1.0);
    }}
}}
""".format(
    buffer_layout=BUFFER_LAYOUT
)


DISPLAY_NORMAL_FRAGMENT_SHADER = """
#version 430

out vec4 Color;

void main()
{
    Color = vec4(1.0, 1.0, 0.0, 1.0); 
}
"""


DISPLAY_LINE_VERTEX_SHADER = """
#version 430

%s

void main()
{
    gl_Position = vec4(world_px[gl_VertexID], world_py[gl_VertexID], 0.0, 1.0);
}
""" % BUFFER_LAYOUT

DISPLAY_LINE_FRAGMENT_SHADER = """
#version 430

out vec4 Color;

void main()
{
    Color = vec4(1.0, 1.0, 0.0, 1.0); 
}
"""


class Resources(object):

    def __init__(self):

        self.display_line_program = None
        self.display_normal_program = None
        self.display_buffer = None
        self.display_vertex_array = None
        self.display_vertex_count = None

    def initialize(self):

        self.display_vertex_count = WORLD_LINE_COUNT * 2

        self.display_line_program = initialize_program(
            initialize_shader(GL_VERTEX_SHADER, DISPLAY_LINE_VERTEX_SHADER),
            initialize_shader(GL_FRAGMENT_SHADER, DISPLAY_LINE_FRAGMENT_SHADER)
        )

        self.display_normal_program = initialize_program(
            initialize_shader(GL_VERTEX_SHADER, DISPLAY_NORMAL_VERTEX_SHADER),
            initialize_shader(GL_FRAGMENT_SHADER, DISPLAY_NORMAL_FRAGMENT_SHADER)
        )

        self.display_buffer = initialize_buffer(prepare_float_buffer_data(
            #prepare_lines(INT0_X) +
            prepare_lines(INT1_X) +
            #prepare_lines(INT0_Y) +
            prepare_lines(INT1_Y)
        ))

        self.display_vertex_array = initialize_vertex_array()

    def dispose(self):

        self.display_line_program = dispose_program(self.display_line_program)
        self.display_normal_program = dispose_program(self.display_normal_program)
        self.display_buffer = dispose_buffer(self.display_buffer)
        self.display_vertex_array = dispose_vertex_array(self.display_vertex_array)
        self.display_vertex_count = None


def bind_buffer(resources):

    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, resources.display_buffer)


def display(resources):

    glBindVertexArray(resources.display_vertex_array)
    glUseProgram(resources.display_line_program)
    bind_buffer(resources)
    glDrawArrays(GL_LINES, 0, resources.display_vertex_count)
    glUseProgram(resources.display_normal_program)
    bind_buffer(resources)
    glDrawArrays(GL_LINES, 0, resources.display_vertex_count)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, 0)
    glUseProgram(0)
    glBindVertexArray(0)
