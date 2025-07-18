from itertools import cycle

from engine.keyboard_hook import KeyboardHook
from engine.keyboard_layouts import KeyboardLayoutsWin

CYCLED_LAYOUTS = cycle(['00000409', '00000419'])
GREEK_LAYOUT = '00000408'


def switch_to_greek():
    KeyboardLayoutsWin.activate_layout(GREEK_LAYOUT)


def next_layout():
    keyboard_layout_id = next(CYCLED_LAYOUTS)
    KeyboardLayoutsWin.activate_layout(keyboard_layout_id)


if __name__ == "__main__":
    available_layouts = KeyboardLayoutsWin.available_keyboard_layouts()
    print(available_layouts)

    hotkey_settings = KeyboardLayoutsWin.disable_hotkeys()

    keyboard = KeyboardHook()
    keyboard.register_callback(frozenset({'ctrl', 'shift'}), switch_to_greek)
    keyboard.register_callback(frozenset({'alt', 'shift'}), next_layout)

    KeyboardLayoutsWin.restore_hotkeys(*hotkey_settings)
