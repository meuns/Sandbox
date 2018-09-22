import glfw

from OpenGL.GL import GL_COLOR_BUFFER_BIT, glViewport, glClear, glClearColor

import Random
import Ray
import World


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

    #for iteration in range(2):
    #    Ray.trace(ray, iteration, world.display_buffer)

    # OpenGL
    glViewport(0, 0, 800, 800)
    glClearColor(0.2, 0.2, 0.2, 0)

    #while not glfw.window_should_close(window):

    glClear(GL_COLOR_BUFFER_BIT)

    World.display(world)

    Random.init(random)

    for iteration in range(4):
        Ray.trace(ray, iteration, world.display_buffer, random.seed_buffer)
        Ray.display_lines(ray, iteration + 1)

    Ray.display_directions(ray, 0)

    # Done !
    glfw.swap_buffers(window)

    while not glfw.window_should_close(window):
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":

    main()
