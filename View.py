# coding: utf8

from OpenGL.GL import glUniformMatrix3fv
from glm import value_ptr


VIEW_PROJECTION_LOCATION = 0

DATA_LAYOUT = """
layout(location = {define_view_projection_location}) uniform mat3 view_projection;
""".format(
    define_view_projection_location=VIEW_PROJECTION_LOCATION
)


def update_view_projection(view_projection):

    glUniformMatrix3fv(VIEW_PROJECTION_LOCATION, 1, False, value_ptr(view_projection))
