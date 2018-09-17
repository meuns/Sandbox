# coding: utf8

from OpenGL.GL import GL_COMPILE_STATUS, GL_LINK_STATUS,\
    glCreateShader, glDeleteShader, glShaderSource, glCompileShader, glGetShaderiv, glGetShaderInfoLog,\
    glCreateProgram, glDeleteProgram, glAttachShader, glLinkProgram, glGetProgramiv, glGetProgramInfoLog


def initialize_shader(shader_type, shader_source):

    shader = glCreateShader(shader_type)
    glShaderSource(shader, shader_source)
    glCompileShader(shader)
    result = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if result == 0:
        raise RuntimeError(glGetShaderInfoLog(shader))
    return shader


def dispose_shader(shader):

    if shader is not None:
        glDeleteShader(shader)


def initialize_program(*shaders):

    program = glCreateProgram()
    for shader in shaders:
        glAttachShader(program, shader)
    glLinkProgram(program)
    for shader in shaders:
        dispose_shader(shader)
    result = glGetProgramiv(program, GL_LINK_STATUS)
    if result == 0:
        raise RuntimeError(glGetProgramInfoLog(program))
    return program


def dispose_program(program):

    if program is not None:
        glDeleteProgram(program)
