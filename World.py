# coding: utf8

from itertools import islice

from OpenGL.GL import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_SHADER_STORAGE_BUFFER, GL_LINES, \
    glBindVertexArray, glUseProgram, glDrawArrays, glBindBufferBase

from glm import mat3

from Shader import initialize_shader, initialize_program, dispose_program
from Buffer import prepare_float_buffer_data, initialize_buffer, dispose_buffer
from Vertex import initialize_vertex_array, dispose_vertex_array

from Config import WORLD_LINE_COUNT, INT_X, INT_Y, INT_IOR_I, INT_IOR_T

from View import update_view_projection, DATA_LAYOUT as VIEW_DATA_LAYOUT


def prepare_lines(line_strip):

    lines = []
    for data0, data1 in zip(islice(line_strip, 0, len(line_strip) - 1), islice(line_strip, 1, None)):
        lines.append(data0)
        lines.append(data1)
    return lines


BUFFER_LAYOUT = """
#define WORLD_LINE_COUNT {define_world_line_count}

layout(std430, binding = 0) buffer World
{{
    float world_pos_x[WORLD_LINE_COUNT << 1];
    float world_pos_y[WORLD_LINE_COUNT << 1];
    float world_ior_i[WORLD_LINE_COUNT];
    float world_ior_t[WORLD_LINE_COUNT];
}};

void get_world_line(uint line_index, out vec2 p0, out vec2 p1, out float ior_i, out float ior_t)
{{
    uint first_point_index = line_index << 1;
    p0 = vec2(world_pos_x[first_point_index + 0], world_pos_y[first_point_index + 0]);
    p1 = vec2(world_pos_x[first_point_index + 1], world_pos_y[first_point_index + 1]);
    ior_i = world_ior_i[line_index];
    ior_t = world_ior_t[line_index];
}}
""".format(
    define_world_line_count=WORLD_LINE_COUNT
)


DISPLAY_NORMAL_VERTEX_SHADER = """
#version 430

{include_view_data_layout}
{include_world_buffer_layout}

void main()
{{
    vec2 p0, p1;
    float ior_i, ior_t;
    get_world_line(gl_VertexID >> 1, p0, p1, ior_t, ior_t);
    
    // pair vertices are normal origins and odd vertices are normal tips
    vec3 position = view_projection * vec3((p0 + p1) * 0.5 + (gl_VertexID % 2 == 0 ? vec2(0.0) : (p1 - p0).yx * vec2(-1.0, 1.0) * 0.25), 1.0);
    
    gl_Position = vec4(position.xy / position.z, 0.0, 1.0);
}}
""".format(
    include_world_buffer_layout=BUFFER_LAYOUT,
    include_view_data_layout=VIEW_DATA_LAYOUT
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

{include_view_data_layout}
{include_world_buffer_layout}

void main()
{{
    vec3 position = view_projection * vec3(world_pos_x[gl_VertexID], world_pos_y[gl_VertexID], 1.0);
    gl_Position = vec4(position.xy / position.z, 0.0, 1.0);
}}
""".format(
    include_world_buffer_layout=BUFFER_LAYOUT,
    include_view_data_layout=VIEW_DATA_LAYOUT
)

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
            sum([prepare_lines(line_strip) for line_strip in INT_X], []) +
            sum([prepare_lines(line_strip) for line_strip in INT_Y], []) +
            sum(INT_IOR_I, []) +
            sum(INT_IOR_T, [])
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


def display(resources, view_projection):

    glBindVertexArray(resources.display_vertex_array)
    glUseProgram(resources.display_line_program)
    bind_buffer(resources)
    update_view_projection(view_projection)
    glDrawArrays(GL_LINES, 0, resources.display_vertex_count)
    glUseProgram(resources.display_normal_program)
    bind_buffer(resources)
    glDrawArrays(GL_LINES, 0, resources.display_vertex_count)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, 0)
    glUseProgram(0)
    glBindVertexArray(0)
