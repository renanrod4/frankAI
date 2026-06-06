# Esse script é responsável por escutar o teclado, detectando o atalho Super + F para iniciar a gravação de áudio

import asyncio
from evdev import InputDevice, list_devices, ecodes

class KeyboardListener:
    def __init__(self, on_press_callback, on_release_callback):
        """
        Gerencia a escuta do teclado em nível de hardware.
        Recebe duas funções (callbacks) que serão executadas nos eventos do atalho.
        """
        self.device = self._find_keyboard()
        self.meta_pressed = False
        self.f_pressed = False
        self.on_press = on_press_callback
        self.on_release = on_release_callback

    def _find_keyboard(self):
        paths = list_devices()
        if not paths:
            raise RuntimeError("Nenhum dispositivo de entrada acessível. Verifique as permissões do grupo input.")

        devices = [InputDevice(path) for path in paths]

        for d in devices:
            if "keyboard" in d.name.lower():
                print(f"Teclado detectado: {d.name} ({d.path})")
                return d

        for d in devices:
            capabilities = d.capabilities()
            if ecodes.EV_KEY in capabilities:
                if ecodes.KEY_ENTER in capabilities[ecodes.EV_KEY]:
                    print(f"Teclado detectado por capacidade: {d.name} ({d.path})")
                    return d

        raise RuntimeError("Nenhum teclado físico compatível foi encontrado.")

    async def monitor_hotkey(self):
        print("Escuta de hardware ativa. Mantenha pressionado Super + F para falar...")
        
        async for event in self.device.async_read_loop():
            if event.type == ecodes.EV_KEY:
                
                # Gerenciamento da tecla Super (Meta/Windows)
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

    async def _trigger_press(self):
        if asyncio.inspect.iscoroutinefunction(self.on_press):
            await self.on_press()
        else:
            self.on_press()

    async def _trigger_release(self):
        if asyncio.inspect.iscoroutinefunction(self.on_release):
            await self.on_release()
        else:
            self.on_release()