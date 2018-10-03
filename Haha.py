import glfw

from OpenGL.GL import GL_COLOR_BUFFER_BIT, glViewport, glClear, glClearColor

from glm import mat3, vec3, vec2, inverse, abs, sign


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


def max_abs(v):

    if abs(v.x) > abs(v.y):
        return v.x
    else:
        return v.y


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
    last_cursor = None
    transform_view = mat3(1.0)
    last_view = mat3(1.0)

    while not glfw.window_should_close(window):

        window_width, window_height = glfw.get_window_size(window)

        projection = mat_projection(window_width, window_height)

        # Pan and zoom
        last_inv_view_projection_viewport = inverse(mat_viewport(window_width, window_height) * projection * last_view)
        next_cursor = (last_inv_view_projection_viewport * vec3(*glfw.get_cursor_pos(window), 1.0)).xy

        next_mouse_left = glfw.get_mouse_button(window, 0)
        if last_mouse_left != next_mouse_left:
            if next_mouse_left:
                last_cursor = next_cursor
            else:
                last_view = current_view
                transform_view = mat3(1.0)
            last_mouse_left = next_mouse_left
        else:
            if next_mouse_left:
                delta_cursor = next_cursor - last_cursor
                transform_view = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, delta_cursor.x, delta_cursor.y, 1.0)

        if not next_mouse_left:
            next_mouse_right = glfw.get_mouse_button(window, 1)
            if last_mouse_right != next_mouse_right:
                if next_mouse_right:
                    last_cursor = next_cursor
                else:
                    last_view = current_view
                    transform_view = mat3(1.0)
                last_mouse_right = next_mouse_right
            else:
                if next_mouse_right:
                    current_view_zoom = max(1.0 + max_abs(next_cursor - last_cursor), 1e-4)
                    pivot = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, last_cursor.x, last_cursor.y, 1.0)
                    inv_pivot = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -last_cursor.x, -last_cursor.y, 1.0)
                    transform_view = pivot * mat3(current_view_zoom, 0.0, 0.0, 0.0, current_view_zoom, 0.0, 0.0, 0.0, 1.0) * inv_pivot

        # Setup view and projection
        current_view = last_view * transform_view
        current_view_projection = projection * current_view

        # Keep random stable through frames
        Random.init(random)

        # Display rays
        glViewport(0, 0, window_width, window_height)
        glClear(GL_COLOR_BUFFER_BIT)

        World.display(world, current_view_projection)

        for iteration in range(10):
            Ray.trace(ray, iteration, world.display_buffer, random.seed_buffer)
            Ray.display_lines(ray, current_view_projection, iteration)

        Ray.display_directions(ray, iteration)

        # Done !
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":

    main()
