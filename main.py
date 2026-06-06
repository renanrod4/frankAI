import asyncio
from evdev import InputDevice, list_devices, ecodes

class KeyboardListener:
    def __init__(self):
        self.device = self._find_keyboard()
        self.meta_pressed = False
        self.f_pressed = False

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
        print("Escuta de hardware ativa. Aguardando Super + F (Mantenha pressionado para falar)...")
        
        async for event in self.device.async_read_loop():
            if event.type == ecodes.EV_KEY:
                
                if event.code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
                    if event.value == 1:
                        self.meta_pressed = True
                    elif event.value == 0:
                        self.meta_pressed = False
                        if self.f_pressed:
                            self.f_pressed = False
                            self.on_hotkey_released()

                elif event.code == ecodes.KEY_F:
                    if event.value == 1 and self.meta_pressed and not self.f_pressed:
                        self.f_pressed = True
                        self.on_hotkey_pressed()
                    elif event.value == 0 and self.f_pressed:
                        self.f_pressed = False
                        self.on_hotkey_released()

    def on_hotkey_pressed(self):
        print("-> [GATILHO] Atalho pressionado. Iniciando gravação do microfone...")

    def on_hotkey_released(self):
        print("-> [GATILHO] Atalho liberado. Parando gravação e enviando para o Whisper...")

async def main():
    try:
        listener = KeyboardListener()
        await listener.monitor_hotkey()
    except PermissionError:
        print("Erro de permissão ao acessar o hardware. Certifique-se de que seu usuário está no grupo input.")
    except KeyboardInterrupt:
        print("\nEncerrando o assistente frankAI.")

if __name__ == "__main__":
    asyncio.run(main())