import ctypes
import winreg
from ctypes import wintypes  # ← добавили

# Define kernel32 Sleep function
kernel32 = ctypes.windll.kernel32
kernel32.Sleep.argtypes = [wintypes.DWORD]  # milliseconds
kernel32.Sleep.restype = None


class KeyboardLayoutsWin:
    _KLID_LAYOUTS_BRANCH = r"SYSTEM\\CurrentControlSet\\Control\\Keyboard Layouts"
    _KLID_PRELOAD_BRANCH = r"Keyboard Layout\\Preload"
    _LAYOUT_TOGGLE_BRANCH = r"Keyboard Layout\\Toggle"
    _KLID_SUBSTITUTES_BRANCH = r"Keyboard Layout\\Substitutes"

    _KLF_ACTIVATE = 0x00000001
    _WM_INPUT_LANG_CHANGE_REQUEST = 0x0050
    _WM_SETTING_CHANGE = 0x001A
    _HWND_BROADCAST = 0xFFFF
    _DISABLED = '3'
    _user32 = ctypes.windll.user32

    # --- добавили явное описание сигнатур WinAPI ------------------------ #
    _user32.PostMessageW.argtypes = (
        wintypes.HWND,  # hWnd
        wintypes.UINT,  # Msg
        wintypes.WPARAM,  # wParam
        wintypes.LPARAM  # lParam
    )
    _user32.PostMessageW.restype = wintypes.BOOL

    _user32.ActivateKeyboardLayout.argtypes = (
        wintypes.HKL,  # hkl
        wintypes.UINT  # Flags
    )
    _user32.ActivateKeyboardLayout.restype = wintypes.HKL


    # ------------------------------------------------------------------ #
    # New internal helper

    @staticmethod
    def _safe_query_value(key, name, default=None):
        """Return a registry value or *default* when the value does not exist."""
        try:
            value, _ = winreg.QueryValueEx(key, name)
            return value
        except FileNotFoundError:
            return default

    # ------------------------------------------------------------------ #
    # Modified public helpers

    @classmethod
    def disable_hotkeys(cls):
        """
        Temporarily set both hot-key switches to “3” (disabled).
        Missing values are tolerated and restored correctly later.
        """
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls._LAYOUT_TOGGLE_BRANCH,
                0,
                winreg.KEY_ALL_ACCESS
        ) as k:
            # remember previous values (may be None)
            lang = cls._safe_query_value(k, "Language Hotkey")
            layout = cls._safe_query_value(k, "Layout Hotkey")

            # write the disabling values
            winreg.SetValueEx(k, "Language Hotkey", 0, winreg.REG_SZ, cls._DISABLED)
            winreg.SetValueEx(k, "Layout Hotkey", 0, winreg.REG_SZ, cls._DISABLED)

        cls.notify()
        return lang, layout

    @classmethod
    def restore_hotkeys(cls, lang, layout):
        """
        Restore the original registry state captured by *disable_hotkeys*.
        Values that were absent originally will be removed again.
        """
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls._LAYOUT_TOGGLE_BRANCH,
                0,
                winreg.KEY_ALL_ACCESS
        ) as k:
            # Language Hotkey
            if lang is None:
                try:
                    winreg.DeleteValue(k, "Language Hotkey")
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(k, "Language Hotkey", 0, winreg.REG_SZ, lang)

            # Layout Hotkey
            if layout is None:
                try:
                    winreg.DeleteValue(k, "Layout Hotkey")
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(k, "Layout Hotkey", 0, winreg.REG_SZ, layout)

        cls.notify()

    @staticmethod
    def _resolve_substitute(klid: str) -> str:

        try:
            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    KeyboardLayoutsWin._KLID_SUBSTITUTES_BRANCH) as subs_key:
                real_klid, _ = winreg.QueryValueEx(subs_key, klid)
                return real_klid
        except FileNotFoundError:
            return klid

    @classmethod
    def notify(cls):
        """
        Broadcast a WM_SETTINGCHANGE so other applications notice
        that the keyboard-layout related registry keys were modified.
        """
        # Create (once) and keep a global buffer that contains
        # the section name "Keyboard Layout" as required by MSDN.
        if not hasattr(cls, "_SETTING_CHANGE_SECTION"):
            # The buffer is automatically NUL-terminated.
            cls._SETTING_CHANGE_SECTION = ctypes.create_unicode_buffer("Keyboard Layout")

        cls._user32.PostMessageW(
            cls._HWND_BROADCAST,
            cls._WM_SETTING_CHANGE,
            0,
            ctypes.cast(cls._SETTING_CHANGE_SECTION, ctypes.c_void_p).value
        )

    @classmethod
    def layout_name(cls, keyboard_layout_id: str) -> str:
        klid = keyboard_layout_id[-8:].upper().rjust(8, "0")

        try:
            with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    fr"{cls._KLID_LAYOUTS_BRANCH}\{klid}") as key:
                name, _ = winreg.QueryValueEx(key, "Layout Text")
                return name
        except FileNotFoundError:
            return "(unknown)"

    @classmethod
    def available_keyboard_layouts(cls) -> dict[str, str]:
        result: dict[str, str] = {}

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls._KLID_PRELOAD_BRANCH) as key:
            i = 0
            while True:
                try:
                    _, klid, _ = winreg.EnumValue(key, i)
                    klid = cls._resolve_substitute(klid)
                    result[klid] = cls.layout_name(klid)
                    i += 1
                except OSError:
                    break
        return result

    @classmethod
    def activate_layout(cls, keyboard_layout: str) -> None:
        keyboard_layout = keyboard_layout[-8:].upper().rjust(8, "0")

        print(f"Loading keyboard layout: {keyboard_layout}")
        hkl = cls._user32.LoadKeyboardLayoutW(keyboard_layout, cls._KLF_ACTIVATE)
        if not hkl:
            err = ctypes.get_last_error()
            raise OSError(f"Failed to load keyboard layout: {err}")

        # Make the layout active for the current thread
        cls._user32.ActivateKeyboardLayout(hkl, 0)

        # Try multiple times to ensure the message is processed
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"Broadcasting keyboard layout change: {keyboard_layout} (attempt {attempt + 1}/{max_attempts})")
            result = cls._user32.PostMessageW(cls._HWND_BROADCAST,
                                              cls._WM_INPUT_LANG_CHANGE_REQUEST,
                                              0, hkl)
            if not result:
                err = ctypes.get_last_error()
                print(f"Warning: PostMessageW failed with error: {err}")

            # Add a small delay to allow the system to process the message
            if attempt < max_attempts - 1:  # Don't sleep after the last attempt
                kernel32.Sleep(100)  # Sleep for 100ms
