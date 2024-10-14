import pyaudio
import numpy as np
import scipy.signal as signal
import wave
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

# Parameter für die Audioaufnahme
CHUNK = 1024          # Anzahl der Samples pro Frame
FORMAT = pyaudio.paInt16  # 16-bit Auflösung
CHANNELS = 1          # Mono
RATE = 44100          # Abtastrate

class RealTimeConvolver:
    def __init__(self, master):
        self.master = master
        self.master.title("Echtzeit-Faltung mit Impulsantworten")
        self.is_recording = False
        self.selected_ir = None
        self.ir_data = None

        self.p = pyaudio.PyAudio()

        # GUI-Komponenten
        self.create_widgets()

        # Lade die Impulsantworten
        self.ir_files = ["Alt Barmbek Klatschen.wav"] #, "ir2.wav", "ir3.wav", "ir4.wav", "ir5.wav"
        self.load_impulse_responses()

    def create_widgets(self):
        # Dropdown für die Auswahl der Impulsantwort
        self.ir_var = tk.StringVar()
        self.ir_var.set("Wähle eine Impulsantwort")
        self.ir_menu = ttk.OptionMenu(self.master, self.ir_var, *["Impulsantwort 1", "Impulsantwort 2", "Impulsantwort 3", "Impulsantwort 4", "Impulsantwort 5"], command=self.select_ir)
        self.ir_menu.pack(pady=10)

        # Start-Button
        self.start_button = ttk.Button(self.master, text="Start", command=self.start_processing)
        self.start_button.pack(pady=5)

        # Stop-Button
        self.stop_button = ttk.Button(self.master, text="Stop", command=self.stop_processing)
        self.stop_button.pack(pady=5)

    def load_impulse_responses(self):
        self.ir_list = []
        for file in self.ir_files:
            wf = wave.open(file, 'rb')
            data = wf.readframes(wf.getnframes())
            ir = np.frombuffer(data, dtype=np.int16)
            self.ir_list.append(ir)
            wf.close()

    def select_ir(self, value):
        index = int(value.split()[-1]) - 1  # Extrahiert die Zahl aus "Impulsantwort X"
        self.ir_data = self.ir_list[index]

    def start_processing(self):
        if self.ir_data is None:
            tk.messagebox.showwarning("Warnung", "Bitte wähle eine Impulsantwort aus.")
            return
        self.is_recording = True
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=CHUNK)
        self.processing_thread = threading.Thread(target=self.process_audio)
        self.processing_thread.start()

    def stop_processing(self):
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()

    def process_audio(self):
        # Normalisiere die Impulsantwort
        ir = self.ir_data / np.max(np.abs(self.ir_data))

        while self.is_recording:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)

            # Faltung
            convolved = signal.convolve(audio_data, ir, mode='same')

            # Verhindere Übersteuerung
            convolved = convolved * (32767 / np.max(np.abs(convolved)))
            convolved = convolved.astype(np.int16)

            # Sende das gefaltete Signal zum Ausgang
            self.stream.write(convolved.tobytes())

    def close(self):
        self.stop_processing()
        self.p.terminate()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RealTimeConvolver(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
