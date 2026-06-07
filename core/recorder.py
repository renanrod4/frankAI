# Esse script é responsável por gravar o áudio do microfone do usuário

import queue
import wave
import os
import numpy as np
import sounddevice as sd

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, output_dir="samples"):

        self.sample_rate = sample_rate
        self.channels = channels
        self.output_dir = output_dir
        self.audio_queue = queue.Queue()
        self.stream = None
        self.recording_path = None

        # Garante que a pasta de `samples` exista para salvar os arquivos de áudio
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"[Recorder] Status do buffer: {status}", flush=True)
        # Coloca os dados de áudio recebidos na fila para processamento
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        # Limpa a fila de áudio para garantir que não haja dados antigos
        while not self.audio_queue.empty():
            self.audio_queue.get()

        self.recording_path = os.path.join(self.output_dir, "input.wav")
        
        # Configura e inicia o stream de áudio 
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            callback=self._audio_callback
        )
        self.stream.start()

    def stop_recording(self):
        if not self.stream:
            return None

        self.stream.stop()
        self.stream.close()
        self.stream = None

        # Coleta todos os dados de áudio da fila e os concatena em um único array
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())

        if not audio_data:
            return None

        full_audio = np.concatenate(audio_data, axis=0)

        # Salva o áudio gravado em um arquivo WAV usando a biblioteca wave
        with wave.open(self.recording_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(full_audio.tobytes())

        return self.recording_path