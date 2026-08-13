# Esse script é responsável por escutar o teclado, detectando o atalho Super + F para iniciar a gravação de áudio

import asyncio
import inspect
from evdev import InputDevice, list_devices, ecodes

class KeyboardListener:
    def __init__(self, on_press_callback, on_release_callback, device_path=None):
        """
        Gerencia a escuta do teclado.
        Recebe dois callbacks e, opcionalmente, um caminho fixo de device.
        """
        self.device = self._find_keyboard(device_path=device_path)
        self.meta_pressed = False
        self.f_pressed = False
        self.on_press = on_press_callback
        self.on_release = on_release_callback

    def _device_has_hotkey(self, device):
        try:
            capabilities = device.capabilities()
        except Exception:
            return False

        if ecodes.EV_KEY not in capabilities:
            return False

        keys = capabilities[ecodes.EV_KEY]
        has_f = ecodes.KEY_F in keys
        has_meta = (ecodes.KEY_LEFTMETA in keys) or (ecodes.KEY_RIGHTMETA in keys)
        return has_f and has_meta

    def _find_keyboard(self, device_path=None):
        candidate_paths = []

        if device_path:
            candidate_paths.append(device_path)

        all_paths = list_devices()
        if not all_paths:
            raise RuntimeError("Nenhum dispositivo de entrada acessível. Verifique as permissões do grupo input.")

        # Prioriza caminhos estáveis do sistema, como os encontrados em /dev/input/by-id/...
        for path in all_paths:
            if "/by-id/" in path or "/by-path/" in path:
                candidate_paths.append(path)

        for path in all_paths:
            if path not in candidate_paths:
                candidate_paths.append(path)

        for path in candidate_paths:
            try:
                device = InputDevice(path)
                name = getattr(device, "name", "").lower()

                if "keyboard" in name and self._device_has_hotkey(device):
                    return device

                if self._device_has_hotkey(device):
                    return device
            except Exception:
                continue

        print("[KeyboardListener] Lista de dispositivos detectados:")
        for path in candidate_paths:
            print(f"  - {path}")
        raise RuntimeError("Nenhum teclado físico com as teclas Super e F foi encontrado.")

    async def monitor_hotkey(self):
        print("Seja bem-vindo ao frankAI! Pressione Super + F para falar com o assistente. Ctrl+C para sair...\n\n")
        try:
            async for event in self.device.async_read_loop():
                if event.type == ecodes.EV_KEY:
                    
                    # Gerenciamento da tecla Super (Meta ou Windows)
                    if event.code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
                        if event.value == 1:
                            self.meta_pressed = True
                        elif event.value == 0:
                            self.meta_pressed = False
                            if self.f_pressed:
                                self.f_pressed = False
                                await self._trigger_release()

                    # Gerenciamento da tecla F
                    elif event.code == ecodes.KEY_F:
                        if event.value == 1 and self.meta_pressed and not self.f_pressed:
                            self.f_pressed = True
                            await self._trigger_press()
                        elif event.value == 0 and self.f_pressed:
                            self.f_pressed = False
                            await self._trigger_release()
        except Exception:
            pass

    async def _trigger_press(self):
        if inspect.iscoroutinefunction(self.on_press):
            await self.on_press()
        else:
            self.on_press()

    async def _trigger_release(self):
        if inspect.iscoroutinefunction(self.on_release):
            await self.on_release()
        else:
            self.on_release()