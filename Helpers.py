from ctypes import sizeof, c_float, c_void_p, c_int
from OpenGL import GL


def list_used_names():

    return (
        [("buffer", name) for name in range(1024) if GL.glIsBuffer(name)] +
        [("framebuffer", name) for name in range(1024) if GL.glIsFramebuffer(name)] +
        [("program", name) for name in range(1024) if GL.glIsProgram(name)] +
        [("program_pipeline", name) for name in range(1024) if GL.glIsProgramPipeline(name)] +
        [("query", name) for name in range(1024) if GL.glIsQuery(name)] +
        [("renderbuffer", name) for name in range(1024) if GL.glIsRenderbuffer(name)] +
        [("sampler", name) for name in range(1024) if GL.glIsSampler(name)] +
        [("shader", name) for name in range(1024) if GL.glIsShader(name)] +
        [("sync", name) for name in range(1024) if GL.glIsSync(name)] +
        [("texture", name) for name in range(1024) if GL.glIsTexture(name)] +
        [("transform_feedback", name) for name in range(1024) if GL.glIsTransformFeedback(name)] +
        [("vertex_array", name) for name in range(1024) if GL.glIsVertexArray(name)]
    )


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

    # We delete these anyways because we will reinitialize the whole things later...
    if delete_shaders:
        for shader in shaders:
            GL.glDeleteShader(shader)

    result = GL.glGetProgramiv(program, GL.GL_LINK_STATUS)
    if result == 0:
        raise RuntimeError(GL.glGetProgramInfoLog(program))

    return program


ATTRIBUTE_SIZE_BY_TYPES = {
    GL.GL_FLOAT_VEC2.real: 2,
    GL.GL_FLOAT_VEC3.real: 3,
    GL.GL_FLOAT_VEC4.real: 4
}


def create_program_attribute_layout(program):

    active_attribute = c_int(0)
    GL.glGetProgramiv(program, GL.GL_ACTIVE_ATTRIBUTES, active_attribute)

    max_name_length = GL.glGetProgramiv(program, GL.GL_ACTIVE_ATTRIBUTE_MAX_LENGTH)
    name_length = GL.GLsizei(0)
    attribute_size = GL.GLint(0)
    attribute_type = GL.GLenum(0)
    name = (GL.GLchar * max_name_length)()

    attribute_layout = []
    for index in range(active_attribute.value):
        GL.glGetActiveAttrib(program, index, max_name_length, name_length, attribute_size, attribute_type, name)
        attribute_location = GL.glGetAttribLocation(program, name.value)
        attribute_layout.append((attribute_location, ATTRIBUTE_SIZE_BY_TYPES[attribute_type.value]))

    attribute_layout.sort(key=lambda pair: pair[0])

    attribute_locations = []
    attribute_sizes = []
    for attribute_location, attribute_size in attribute_layout:
        attribute_locations.append(attribute_location)
        attribute_sizes.append(attribute_size)

    return attribute_locations, attribute_sizes


def validate_attribute_bindings(program_layout_locations, program_attribute_sizes, vertex_array_layout_locations, vertex_array_attribute_sizes):

    if program_layout_locations != vertex_array_layout_locations:
        raise RuntimeError("Program and vertex array attribute layouts don't match (%s != %s)" %
                           (program_layout_locations, vertex_array_layout_locations))

    if program_attribute_sizes != vertex_array_attribute_sizes:
        raise RuntimeError("Program and vertex array attribute sizes don't match (%s != %s)" %
                           (program_attribute_sizes, vertex_array_attribute_sizes))


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

    attribute_locations = list(vertex_data.keys())
    attribute_locations.sort()

    vertex_count = len(vertex_data[attribute_locations[0]])

    flat_vertex_data = []
    for attribute_location in attribute_locations:
        flat_vertex_data.append([x for vertex in vertex_data[attribute_location] for x in vertex])

    attribute_sizes = [len(vertex_data[attribute_location][0]) for attribute_location in attribute_locations]

    attribute_offsets = [c_void_p(sizeof(len(flat_attribute_data) * c_float)) for flat_attribute_data in flat_vertex_data]
    attribute_offsets = [c_void_p(0)] + attribute_offsets[:-1]

    vertex_buffer_data = []
    for flat_attribute_data in flat_vertex_data:
        vertex_buffer_data.extend(flat_attribute_data)

    return attribute_locations, attribute_sizes, attribute_offsets, vertex_buffer_data, vertex_count


def create_vertex_array_and_draw_call(layout_locations, attribute_sizes, attribute_offsets, vertex_buffer_data, vertex_count):

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

    def draw_call():
        GL.glBindVertexArray(vertex_array)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, vertex_count)
        GL.glBindVertexArray(0)

    return vertex_array, draw_call
