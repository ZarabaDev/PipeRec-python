"""
PipeRec - Dual Audio Capture Engine
Pure PulseAudio Implementation (Parec Only).
"""

import os
import wave
import threading
import queue
import time
import subprocess
import numpy as np
from datetime import datetime

class ParecordCapture(threading.Thread):
    def __init__(self, source_name: str, queue: queue.Queue, sample_rate: int = 44100):
        super().__init__(daemon=True)
        self.source_name = source_name
        self.queue = queue
        self.sample_rate = sample_rate
        self.stop_event = threading.Event()
        self.process = None
    
    def run(self):
        try:
            cmd = [
                'parec',
                '--format=s16le',
                f'--rate={self.sample_rate}',
                '--channels=1', # Capture mono directly
                f'--device={self.source_name}',
                '--latency-msec=50'
            ]
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            
            chunk_size = 4096 * 2 # 4096 samples * 2 bytes
            
            while not self.stop_event.is_set():
                if self.process:
                    data = self.process.stdout.read(chunk_size)
                    if data:
                        self.queue.put(data)
                    else:
                        time.sleep(0.01)
                else:
                    break
        except Exception as e:
            print(f"Parec error: {e}")
        finally:
            self._cleanup()

    def stop(self):
        self.stop_event.set()
        self._cleanup()
        
    def _cleanup(self):
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
            self.process = None

class DualAudioCapture:
    SAMPLE_RATE = 44100
    
    def __init__(self, output_dir="recordings", temp_dir="temp"):
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        
        # State
        self.is_monitoring = False
        self.is_recording = False
        self.is_paused = False
        
        # Queues
        self.mic_queue = queue.Queue()
        self.sys_queue = queue.Queue()
        
        # Levels
        self.mic_level = -100.0
        self.sys_level = -100.0
        
        # Threads
        self.mic_thread = None
        self.sys_thread = None
        self.processor_thread = None
        self.processor_stop = threading.Event()
        
        # WAVs
        self.mic_wav = None
        self.sys_wav = None
        self.start_time = None

    def _process_audio_loop(self):
        """Consume queues, update levels, write to disk."""
        while not self.processor_stop.is_set():
            # MIC
            try:
                data = self.mic_queue.get(timeout=0.005)
                # Level
                arr = np.frombuffer(data, dtype=np.int16)
                if len(arr) > 0:
                    peak = np.max(np.abs(arr[::20])) # Subsample
                    self.mic_level = 20 * np.log10(peak / 32768) if peak > 0 else -100.0
                
                if self.is_recording and not self.is_paused and self.mic_wav:
                    self.mic_wav.writeframes(data)
            except queue.Empty:
                pass

            # SYSTEM
            try:
                data = self.sys_queue.get(timeout=0.005)
                # Level
                arr = np.frombuffer(data, dtype=np.int16)
                if len(arr) > 0:
                    peak = np.max(np.abs(arr[::20]))
                    self.sys_level = 20 * np.log10(peak / 32768) if peak > 0 else -100.0
                
                if self.is_recording and not self.is_paused and self.sys_wav:
                    self.sys_wav.writeframes(data)
            except queue.Empty:
                pass

    def start_monitoring(self, mic_pulse, mon_pulse, *args):
        self.stop_monitoring()
        
        # Clear queues
        self.mic_queue = queue.Queue()
        self.sys_queue = queue.Queue()
        
        self.processor_stop.clear()
        self.processor_thread = threading.Thread(target=self._process_audio_loop, daemon=True)
        self.processor_thread.start()
        
        if mic_pulse:
            self.mic_thread = ParecordCapture(mic_pulse, self.mic_queue)
            self.mic_thread.start()
            
        if mon_pulse:
            self.sys_thread = ParecordCapture(mon_pulse, self.sys_queue)
            self.sys_thread.start()
            
        self.is_monitoring = True
        return True

    def stop_monitoring(self):
        self.is_monitoring = False
        self.is_recording = False
        
        if self.mic_thread: self.mic_thread.stop()
        if self.sys_thread: self.sys_thread.stop()
        
        self.processor_stop.set()
        if self.processor_thread: self.processor_thread.join(timeout=1.0)

    def start_recording(self):
        if not self.is_monitoring: return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.mic_temp = os.path.join(self.temp_dir, f"mic_{timestamp}.wav")
        self.sys_temp = os.path.join(self.temp_dir, f"sys_{timestamp}.wav")
        
        self.mic_wav = wave.open(self.mic_temp, 'wb')
        self.mic_wav.setnchannels(1)
        self.mic_wav.setsampwidth(2)
        self.mic_wav.setframerate(self.SAMPLE_RATE)
        
        self.sys_wav = wave.open(self.sys_temp, 'wb')
        self.sys_wav.setnchannels(1)
        self.sys_wav.setsampwidth(2)
        self.sys_wav.setframerate(self.SAMPLE_RATE)
        
        self.start_time = time.time()
        self.is_paused = False
        self.is_recording = True
        return True

    def stop_recording(self):
        if not self.is_recording: return None, None
        self.is_recording = False
        time.sleep(0.5) 
        
        if self.mic_wav: self.mic_wav.close()
        if self.sys_wav: self.sys_wav.close()
        
        return self.mic_temp, self.sys_temp

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def get_levels(self):
        # Decay
        self.mic_level = max(-100, self.mic_level - 2.0)
        self.sys_level = max(-100, self.sys_level - 2.0)
        return self.mic_level, self.sys_level
