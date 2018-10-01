import glfw

from OpenGL.GL import GL_COLOR_BUFFER_BIT, glViewport, glClear, glClearColor

from glm import mat3, vec3, vec2


import Random
import Ray
import World


def mat_view(view_offset):

    return mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, view_offset[0], view_offset[1], 1.0)


def mat_projection(window_width, window_height):

    if window_width > window_height:
        window_aspect = window_width / window_height
        return mat3(1.0 / window_aspect, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    else:
        window_aspect = window_height / window_width
        return mat3(1.0, 0.0, 0.0, 0.0, 1.0 / window_aspect, 0.0, 0.0, 0.0, 1.0)


def mat_inv_projection(window_width, window_height):

    if window_width > window_height:
        window_aspect = window_width / window_height
        return mat3(window_aspect, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    else:
        window_aspect = window_height / window_width
        return mat3(1.0, 0.0, 0.0, 0.0, window_aspect, 0.0, 0.0, 0.0, 1.0)


def mat_viewport(window_width, window_height):

    return mat3(window_width / 2.0, 0.0, 0.0, 0.0, -window_height / 2.0, 0.0, window_width / 2.0, window_height / 2.0, 1.0)


def mat_inv_viewport(window_width, window_height):

    return mat3(2.0 / window_width, 0.0, 0.0, 0.0, -2.0 / window_height, 0.0, -1.0, +1.0, 1.0)


def main():

    if not glfw.init():
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(800, 800, "Hello World", None, None)
    if not window:
        glfw.terminate()
        return

    # Make the window's context current
    glfw.make_context_current(window)
    
    # Enable VSync
    glfw.swap_interval(1)

    # World
    world = World.Resources()
    world.initialize()

    ray = Ray.Resources()
    ray.initialize()

    random = Random.Resources()
    random.initialize()

    # OpenGL
    glClearColor(0.2, 0.2, 0.2, 0)

    # Pan and zoom
    last_mouse_left = 0
    last_cursor = None
    last_view_offset = vec2(0.0, 0.0)
    current_view_offset = vec2(0.0, 0.0)

    while not glfw.window_should_close(window):

        window_width, window_height = glfw.get_window_size(window)

        next_mouse_left = glfw.get_mouse_button(window, 0)
        if last_mouse_left != next_mouse_left:
            next_cursor_mat = mat_inv_projection(window_width, window_height) * mat_inv_viewport(window_width, window_height)
            next_cursor_x, next_cursor_y = glfw.get_cursor_pos(window)
            next_cursor = (next_cursor_mat * vec3(next_cursor_x, next_cursor_y, 1.0)).xy
            if next_mouse_left:
                last_cursor = next_cursor
            else:
                last_view_offset = last_view_offset + (next_cursor - last_cursor)
                current_view_offset = vec2(0.0, 0.0)
            last_mouse_left = next_mouse_left
        else:
            if next_mouse_left:
                next_cursor_mat = mat_inv_projection(window_width, window_height) * mat_inv_viewport(window_width, window_height)
                next_cursor_x, next_cursor_y = glfw.get_cursor_pos(window)
                next_cursor = (next_cursor_mat * vec3(next_cursor_x, next_cursor_y, 1.0)).xy
                current_view_offset = next_cursor - last_cursor

        # Setup view and projection
        view_projection = mat_projection(window_width, window_height) * mat_view(last_view_offset + current_view_offset)

        # Keep random stable through frames
        Random.init(random)

        # Display rays
        glViewport(0, 0, window_width, window_height)
        glClear(GL_COLOR_BUFFER_BIT)

        World.display(world, view_projection)

        for iteration in range(4):
            Ray.trace(ray, iteration, world.display_buffer, random.seed_buffer)
            Ray.display_lines(ray, view_projection, iteration)

        Ray.display_directions(ray, 0)

        # Done !
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":

    main()
