# coding: utf8

from OpenGL.GL import GLuint, glGenVertexArrays, glDeleteVertexArrays


def initialize_vertex_array():

    vertex_array = GLuint(0)
    glGenVertexArrays(1, vertex_array)
    return vertex_array


def dispose_vertex_array(vertex_array):

    if vertex_array is not None:
        glDeleteVertexArrays(1, (vertex_array,))
