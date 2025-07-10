import keyboard


class Keyboard:
    def __init__(self):
        self._pressed = set()
        self._active = set()
        self._hotkeys = set()
        self._hotkeys_to_callback = {}
        self._keyboard = keyboard

        self._keyboard.hook(self._handler)

    def __del__(self):
        keyboard.unhook(self._handler)

    def register_callback(self, keys: frozenset, callback: callable):
        self._hotkeys.update(keys)
        self._hotkeys_to_callback[keys] = callback

    def wait(self):
        self._keyboard.wait('esc')

    @staticmethod
    def _normalize(name: str) -> str:
        return name.replace('left ', '').replace('right ', '')

    def _handler(self, event: keyboard.KeyboardEvent):
        key = self._normalize(event.name)

        if key not in self._hotkeys:
            return

        if event.event_type == keyboard.KEY_DOWN:
            self._pressed.add(key)
        else:
            self._pressed.discard(key)

        for combo, callback in self._hotkeys_to_callback.items():
            if combo.issubset(self._pressed):
                if combo not in self._active:
                    callback()
                    self._active.add(combo)
            else:
                self._active.discard(combo)
