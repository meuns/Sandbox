# coding: utf8

from OpenGL.GL import GL_SHADER_STORAGE_BUFFER, GL_STATIC_DRAW, \
    GLuint, GLfloat, sizeof,\
    glGenBuffers, glDeleteBuffers, glBindBuffer, glBufferData


def prepare_float_buffer_data(float_array):

    buffer_data_type = GLfloat * len(float_array)
    return sizeof(buffer_data_type), buffer_data_type(*float_array)


def prepare_uint_buffer_data(int_array):

    buffer_data_type = GLuint * len(int_array)
    return sizeof(buffer_data_type), buffer_data_type(*int_array)


def initialize_buffer(buffer_data_size, buffer_data=None, buffer_usage=GL_STATIC_DRAW):

    if buffer_data is None:
        buffer_data_size, buffer_data = buffer_data_size

    buffer = GLuint(0)
    glGenBuffers(1, buffer)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buffer)
    glBufferData(GL_SHADER_STORAGE_BUFFER, buffer_data_size, buffer_data, buffer_usage)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)
    return buffer


def dispose_buffer(buffer):

    if buffer is not None:
        glDeleteBuffers(1, (buffer,))
