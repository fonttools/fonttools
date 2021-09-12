import fontTools
import pytest


@pytest.fixture(autouse=True, scope="session")
def disableConfigLogger():
    """Session-scoped fixture to make fontTools.configLogger function no-op.

    Logging in python maintains a global state. When in the tests we call a main()
    function from modules subset or ttx, a call to configLogger is made that modifies
    this global state (to configures a handler for the fontTools logger).
    To prevent that, we monkey-patch the `configLogger` attribute of the `fontTools`
    module (the one used in the scripts main() functions) so that it does nothing,
    to avoid any side effects.

    NOTE: `fontTools.configLogger` is only an alias for the configLogger function in
    `fontTools.misc.loggingTools` module; the original function is not modified.
    """

    def noop(*args, **kwargs):
        return

    originalConfigLogger = fontTools.configLogger
    fontTools.configLogger = noop
    try:
        yield
    finally:
        fontTools.configLogger = originalConfigLogger
