from ctypes import sizeof, c_float, c_void_p
from OpenGL import GL


def compile_shader(source, shader_type):

    shader = GL.glCreateShader(shader_type)
    GL.glShaderSource(shader, source)

    GL.glCompileShader(shader)
    result = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
    if result == 0:
        raise RuntimeError(GL.glGetShaderInfoLog(shader))

    return shader


def link_program(*shaders, delete_shaders=True):

    program = GL.glCreateProgram()
    for shader in shaders:
        GL.glAttachShader(program, shader)

    GL.glLinkProgram(program)
    result = GL.glGetProgramiv(program, GL.GL_LINK_STATUS)
    if result == 0:
        raise RuntimeError(GL.glGetProgramInfoLog(program))

    if delete_shaders:
        for shader in shaders:
            GL.glDeleteShader(shader)

    return program


def validate_vertex_data(vertex_data):

    layout_locations = list(vertex_data.keys())
    if len(layout_locations) != len(set(layout_locations)):
        raise RuntimeError("Vertex data layout locations should be unique")

    attribute_count = len(vertex_data[layout_locations[0]])
    for layout_location in layout_locations[1:]:
        if len(vertex_data[layout_location]) != attribute_count:
            raise RuntimeError("Vertex data attributes must share count")

    for layout_location in layout_locations:
        attribute_size = len(vertex_data[layout_location][0])
        for attribute in vertex_data[layout_location]:
            if len(attribute) != attribute_size:
                raise RuntimeError("Vertex data attributes must share size")

    return vertex_data


def flatten_vertex_data(vertex_data):

    layout_locations = list(vertex_data.keys())
    layout_locations.sort()

    flattened_vertex_data = []
    for layout_location in layout_locations:
        flattened_vertex_data.append([x for vertex in vertex_data[layout_location] for x in vertex])

    attribute_sizes = [len(vertex_data[layout_location][0]) for layout_location in layout_locations]

    attribute_offsets = [c_void_p(sizeof(len(flattened_attribute_data) * c_float)) for flattened_attribute_data in flattened_vertex_data]
    attribute_offsets = [c_void_p(0)] + attribute_offsets[:-1]

    vertex_buffer_data = []
    for flattened_attribute_data in flattened_vertex_data:
        vertex_buffer_data.extend(flattened_attribute_data)

    return layout_locations, attribute_sizes, attribute_offsets, vertex_buffer_data


def create_vertex_array(layout_locations, attribute_sizes, attribute_offsets, vertex_buffer_data):

    vertex_buffer_type = len(vertex_buffer_data) * c_float
    vertex_buffer = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeof(vertex_buffer_type), vertex_buffer_type(*vertex_buffer_data), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    vertex_array = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(vertex_array)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
    for layout_location, attribute_size, attribute_offset in zip(layout_locations, attribute_sizes, attribute_offsets):
        GL.glEnableVertexAttribArray(layout_location)
        GL.glVertexAttribPointer(layout_location, attribute_size, GL.GL_FLOAT, False, 0, attribute_offset)
    GL.glBindVertexArray(0)
    GL.glDeleteBuffers(1, [vertex_buffer])

    return vertex_array
