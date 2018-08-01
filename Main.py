import glfw
import importlib


def main():

    # Initialize the library
    if not glfw.init():
        return

    # Create a windowed mode window and its OpenGL context
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
    window = glfw.create_window(640, 480, "Sandbox", None, None)
    if not window:
        glfw.terminate()
        return

    # Make the window's context current
    glfw.make_context_current(window)

    # Resources
    module = importlib.import_module("Toy")

    frame_size = glfw.get_framebuffer_size(window)
    resources = module.Resources()
    resources.initialize(frame_size)

    # Loop until the user closes the window
    key_r_was_pressed = False

    while not glfw.window_should_close(window):

        # Handle resizing
        last_frame_size = frame_size
        frame_size = glfw.get_framebuffer_size(window)
        if frame_size != last_frame_size:
            resources.dispose()
            resources.initialize(frame_size)

        # Handle shortcuts
        key_r_is_pressed = bool(glfw.get_key(window, glfw.KEY_R))
        key_ctrl_is_pressed = bool(glfw.get_key(window, glfw.KEY_LEFT_CONTROL))
        if key_r_is_pressed is False and key_r_was_pressed is True and key_ctrl_is_pressed is True:
            resources.dispose()
            importlib.reload(module)
            resources = module.Resources()
            resources.initialize(frame_size)

        key_r_was_pressed = key_r_is_pressed

        # Render some shit
        module.render(resources, frame_size)

        # Swap front and back buffers
        glfw.swap_buffers(window)

        # Poll for and process events
        glfw.poll_events()

    resources.dispose()

    glfw.terminate()


if __name__ == "__main__":

    main()
