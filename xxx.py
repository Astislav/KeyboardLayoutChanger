import time

from engine.keyboard_hook import KeyboardHook
from engine.keyboard_layout_manager import KeyboardLayoutManager
from engine.windows.keyboard_layout_registry import WindowsKeyboardLayoutsRegistry
from engine.windows.keyboard_layout_switching_settings import WindowsKeyboardLayoutSwitchingSettings

if __name__ == "__main__":
    settings = WindowsKeyboardLayoutSwitchingSettings()
    registry = WindowsKeyboardLayoutsRegistry()
    hook = KeyboardHook()

    manager = KeyboardLayoutManager(settings, registry, hook)
    manager.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    manager.stop()
    manager.join(timeout=2.0)
