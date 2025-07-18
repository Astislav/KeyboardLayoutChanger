from threading import Thread

from engine.interfaces.keyboard_hook_intreface import KeyboardHookInterface
from engine.interfaces.keyboard_layout_registry_interface import KeyboardLayoutRegistryInterface
from engine.interfaces.keyboard_layout_switching_settings_interface import KeyboardLayoutSwitchingSettingsInterface


class KeyboardLayoutManager(Thread):
    def __init__(
            self,
            keyboard_layout_switching_settings_interface: KeyboardLayoutSwitchingSettingsInterface,
            keyboard_layout_registry: KeyboardLayoutRegistryInterface,
            keyboard_hook: KeyboardHookInterface
    ):
        self._keyboard_hook = keyboard_hook
        self._keyboard_layout_switching_settings_interface = keyboard_layout_switching_settings_interface
        self._keyboard_layout_registry = keyboard_layout_registry
        self._stopped = False

        super().__init__()

    def run(self):
        print('starting keyboard layout manager thread...')
        print(self._keyboard_layout_registry.layouts())

        self._keyboard_layout_switching_settings_interface.disable_system_hotkeys()
        while not self._stopped:
            self._keyboard_hook.process_events()

        self._keyboard_layout_switching_settings_interface.restore_system_hotkeys()
        print('stopped keyboard layout manager thread...')

    def stop(self):
        self._stopped = True
