from OpenGL import GL
import glm
import importlib
import Helpers
importlib.reload(Helpers)

from Helpers import compile_shader, link_program, create_program_attribute_layout, create_vertex_array_and_draw_call,\
    flatten_vertex_data, validate_vertex_data, validate_attribute_bindings


def create_cube(s):

    return {
        0: [
            # Y-
            (-s, -s, -s, 1.0),
            (+s, -s, -s, 1.0),
            (+s, -s, +s, 1.0),
            (-s, -s, -s, 1.0),
            (+s, -s, +s, 1.0),
            (-s, -s, +s, 1.0),

            # X+
            (+s, -s, -s, 1.0),
            (+s, +s, -s, 1.0),
            (+s, +s, +s, 1.0),
            (+s, -s, -s, 1.0),
            (+s, +s, +s, 1.0),
            (+s, -s, +s, 1.0),

            # Y+
            (+s, +s, -s, 1.0),
            (-s, +s, -s, 1.0),
            (-s, +s, +s, 1.0),
            (+s, +s, -s, 1.0),
            (-s, +s, +s, 1.0),
            (+s, +s, +s, 1.0),

            # X-
            (-s, +s, -s, 1.0),
            (-s, -s, -s, 1.0),
            (-s, -s, +s, 1.0),
            (-s, +s, -s, 1.0),
            (-s, -s, +s, 1.0),
            (-s, +s, +s, 1.0),

            # Z-
            (+s, -s, -s, 1.0),
            (-s, +s, -s, 1.0),
            (+s, +s, -s, 1.0),
            (+s, -s, -s, 1.0),
            (-s, -s, -s, 1.0),
            (-s, +s, -s, 1.0),

            # Z+
            (-s, -s, +s, 1.0),
            (+s, -s, +s, 1.0),
            (+s, +s, +s, 1.0),
            (-s, -s, +s, 1.0),
            (+s, +s, +s, 1.0),
            (-s, +s, +s, 1.0),
        ],
        1: [
            # Y-
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),

            # X+
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),

            # Y+
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),

            # X-
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),

            # Z-
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),

            # Z+
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
        ],
    }


class Resources(object):

    def __init__(self, resources=None):

        if resources is None:
            self.cube_vertex_array = 0
            self.cube_draw_call = None
            self.program = 0
        else:
            self.cube_vertex_array = resources.cube_vertex_array
            self.cube_draw_call = resources.cube_draw_call
            self.program = resources.program

    def initialize(self, _frame_size):

        # Program
        with open("Dummy.vert") as vertex_shader_file:
            vertex_shader = compile_shader(vertex_shader_file.readlines(), GL.GL_VERTEX_SHADER)

        with open("Dummy.frag") as pixel_shader_file:
            pixel_shader = compile_shader(pixel_shader_file.readlines(), GL.GL_FRAGMENT_SHADER)

        program = link_program(vertex_shader, pixel_shader)
        self.program = program

        # Cube
        flat_vertex_data = flatten_vertex_data(validate_vertex_data(create_cube(0.5)))
        cube_vertex_array, cube_draw_call = create_vertex_array_and_draw_call(*flat_vertex_data)
        self.cube_vertex_array = cube_vertex_array
        self.cube_draw_call = cube_draw_call

        # Validate both
        validate_attribute_bindings(*create_program_attribute_layout(program), *flat_vertex_data[:2])

    def dispose(self):

        GL.glDeleteVertexArrays(1, [self.cube_vertex_array])
        self.cube_vertex_array = 0

        self.cube_draw_call = None

        GL.glDeleteProgram(self.program)
        self.program = 0


def render(resources, frame_size, elapsed_time):

    GL.glClearColor(0.2, 0.2, 0.2, 0.0)
    GL.glClearDepth(1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_CULL_FACE)

    model_view_projection = (
        glm.perspective(45.0, frame_size[0] / frame_size[1], 0.1, 10000.0) *
        glm.lookAt(glm.vec3(3.0, 3.0, 3.0), glm.vec3(0.0, 0.0, 0.0), glm.vec3(0.0, 0.0, 1.0)) *
        glm.rotate(glm.mat4(1.0), elapsed_time, glm.vec3(1.0, 0.0, 0.0))
    )

    GL.glUseProgram(resources.program)
    GL.glUniformMatrix4fv(0, 1, False, glm.value_ptr(model_view_projection))
    resources.cube_draw_call()
    GL.glUseProgram(0)

    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_CULL_FACE)


def dispose_render():

    GL.glBindVertexArray(0)
    GL.glUseProgram(0)
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_CULL_FACE)