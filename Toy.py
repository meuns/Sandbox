from OpenGL import GL
from Helpers import compile_shader, link_program, create_vertex_array, flatten_vertex_data, validate_vertex_data


def create_quad(s):

    return {
        0: [
            (-s, -s, 0.0, 1.0),
            (+s, -s, 0.0, 1.0),
            (+s, +s, 0.0, 1.0),
            (-s, -s, 0.0, 1.0),
            (+s, +s, 0.0, 1.0),
            (-s, +s, 0.0, 1.0)
        ],
        2: [
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (1.0, 0.0, 1.0),
            (1.0, 1.0, 0.0),
            (1.0, 0.0, 1.0),
            (1.0, 0.0, 0.0),
        ]
    }


class Resources(object):

    def __init__(self):

        self.vertex_array = None
        self.program = None

    def initialize(self, _frame_size):

        # Program
        with open("Dummy.vert") as vertex_shader_file:
            vertex_shader = compile_shader(vertex_shader_file.readlines(), GL.GL_VERTEX_SHADER)

        with open("Dummy.frag") as pixel_shader_file:
            pixel_shader = compile_shader(pixel_shader_file.readlines(), GL.GL_FRAGMENT_SHADER)

        self.program = link_program(vertex_shader, pixel_shader)

        # Vertex array
        vertex_array = create_vertex_array(*flatten_vertex_data(validate_vertex_data(create_quad(0.5))))
        self.vertex_array = vertex_array

    def dispose(self):

        GL.glDeleteProgram(self.program)
        GL.glDeleteVertexArrays(1, [self.vertex_array])
        self.vertex_array = None
        self.program = None


def render(resources, _frame_size):

    GL.glClearColor(0.0, 0.0, 1.0, 0.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    GL.glUseProgram(resources.program)
    GL.glBindVertexArray(resources.vertex_array)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
    GL.glBindVertexArray(0)
    GL.glUseProgram(0)
