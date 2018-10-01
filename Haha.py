import glfw

from OpenGL.GL import GL_COLOR_BUFFER_BIT, glViewport, glClear, glClearColor

from glm import mat3

import Random
import Ray
import World


def fit_viewport_projection(window_width, window_height):

    if window_width < 1 or window_height < 1:
        return mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

    if window_width > window_height:
        window_aspect = window_width / window_height
        return mat3(1.0 / window_aspect, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    else:
        window_aspect = window_height / window_width
        return mat3(1.0, 0.0, 0.0, 0.0, 1.0 / window_aspect, 0.0, 0.0, 0.0, 1.0)


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

    # World
    world = World.Resources()
    world.initialize()

    ray = Ray.Resources()
    ray.initialize()

    random = Random.Resources()
    random.initialize()

    # OpenGL
    glClearColor(0.2, 0.2, 0.2, 0)

    while not glfw.window_should_close(window):

        # Setup view and projection
        window_width, window_height = glfw.get_window_size(window)
        projection = fit_viewport_projection(window_width, window_height)
        view_projection = projection

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
