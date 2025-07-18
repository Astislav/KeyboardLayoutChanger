class KeyboardLayout:
    def __init__(self, system_name: str, system_id: str):
        self._system_name = system_name
        self._system_id = self._normalize_id(system_id)

    @staticmethod
    def _normalize_id(system_id: str) -> str:
        return system_id[-8:].upper().rjust(8, "0")

    @property
    def system_name(self) -> str:
        return self._system_name

    @property
    def system_id(self) -> str:
        return self._system_id

    def __repr__(self):
        return f"{self._system_name} ({self._system_id})"
