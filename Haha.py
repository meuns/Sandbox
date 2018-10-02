import glfw

from OpenGL.GL import GL_COLOR_BUFFER_BIT, glViewport, glClear, glClearColor

from glm import mat3, vec3, vec2, distance


import Random
import Ray
import World


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
    last_mouse_right = 0
    last_cursor_left = None
    last_view_offset = vec2(0.0, 0.0)
    current_view_offset = vec2(0.0, 0.0)
    last_view_zoom = 1.0
    current_view_zoom = 0.0

    last_view = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    current_view = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

    while not glfw.window_should_close(window):

        window_width, window_height = glfw.get_window_size(window)

        next_cursor_mat = mat_inv_projection(window_width, window_height) * mat_inv_viewport(window_width, window_height)
        next_cursor = (next_cursor_mat * vec3(*glfw.get_cursor_pos(window), 1.0)).xy

        next_mouse_left = glfw.get_mouse_button(window, 0)
        if last_mouse_left != next_mouse_left:
            if next_mouse_left:
                last_cursor_left = next_cursor
            else:
                last_view = last_view * current_view
                current_view = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
            last_mouse_left = next_mouse_left
        else:
            if next_mouse_left:
                delta_cursor = next_cursor - last_cursor_left
                current_view = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, delta_cursor.x, delta_cursor.y, 1.0)

        if not next_mouse_left:
            next_mouse_right = glfw.get_mouse_button(window, 1)
            if last_mouse_right != next_mouse_right:
                if next_mouse_right:
                    last_cursor_left = next_cursor
                else:
                    last_view = last_view * current_view
                    current_view = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
                last_mouse_right = next_mouse_right
            else:
                if next_mouse_right:
                    current_view_zoom = 1.0 + (next_cursor.y - last_cursor_left.y)
                    current_view = mat3(current_view_zoom, 0.0, 0.0, 0.0, current_view_zoom, 0.0, 0.0, 0.0, 1.0)

        # Setup view and projection
        view_projection = mat_projection(window_width, window_height) * (last_view * current_view)

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
