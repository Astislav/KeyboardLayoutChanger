from abc import ABC, abstractmethod


class KeyboardLayoutSwitchingSettingsInterface(ABC):
    @abstractmethod
    def disable_system_hotkeys(self):
        pass

    @abstractmethod
    def restore_system_hotkeys(self):
        pass
