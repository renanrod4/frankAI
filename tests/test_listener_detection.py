import importlib
import sys
import types
import unittest
from unittest.mock import patch


class FakeInputDevice:
    def __init__(self, path):
        self.path = path
        self.name = {
            "/dev/input/by-id/usb-keyboard-event-kbd": "USB Keyboard",
            "/dev/input/by-id/usb-mouse-event-mouse": "USB Mouse",
            "/dev/input/event0": "AT Translated Set 2 keyboard",
            "/dev/input/event1": "SynPS/2 Synaptics TouchPad",
        }.get(path, "Generic Device")

    def capabilities(self):
        if self.path in (
            "/dev/input/by-id/usb-keyboard-event-kbd",
            "/dev/input/event0",
        ):
            return {1: [28, 33, 125, 126]}
        return {1: [0]}


class FakeEvdev(types.SimpleNamespace):
    EV_KEY = 1
    KEY_ENTER = 28
    KEY_F = 33
    KEY_LEFTMETA = 125
    KEY_RIGHTMETA = 126


class KeyboardDetectionTests(unittest.TestCase):
    def setUp(self):
        fake_evdev = FakeEvdev(
            InputDevice=FakeInputDevice,
            list_devices=lambda: [
                "/dev/input/by-id/usb-mouse-event-mouse",
                "/dev/input/event1",
                "/dev/input/by-id/usb-keyboard-event-kbd",
                "/dev/input/event0",
            ],
            ecodes=FakeEvdev(),
        )
        self.fake_evdev = fake_evdev

    def test_explicit_device_path_is_used_when_provided(self):
        with patch.dict(sys.modules, {"evdev": self.fake_evdev}):
            import core.listener as listener_module

            importlib.reload(listener_module)
            device = listener_module.KeyboardListener(
                on_press_callback=lambda: None,
                on_release_callback=lambda: None,
                device_path="/dev/input/by-id/usb-keyboard-event-kbd",
            )
            self.assertEqual(
                device.device.path, "/dev/input/by-id/usb-keyboard-event-kbd"
            )

    def test_keyboard_is_preferred_over_mouse_even_if_not_first_in_list(self):
        with patch.dict(sys.modules, {"evdev": self.fake_evdev}):
            import core.listener as listener_module

            importlib.reload(listener_module)
            device = listener_module.KeyboardListener(
                on_press_callback=lambda: None,
                on_release_callback=lambda: None,
            )
            self.assertIn("keyboard", device.device.name.lower())


if __name__ == "__main__":
    unittest.main()
