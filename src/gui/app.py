"""
PipeRec - Professional Main Application Window
Pure Tkinter implementation with stability improvements.
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.audio.devices import list_microphone_devices, list_monitor_devices
from src.audio.capture import DualAudioCapture
from src.audio.processor import AudioProcessor
from src.gui.components import (
    VUMeterCanvas, TimerDisplay, RecordButton, StopButton,
    DeviceDropdown, StatusBar
)
from src.gui.theme import COLORS, FONTS, DIMENSIONS, ANIMATIONS, configure_ttk_styles


class PipeRecApp:
    """Main application window with professional interface."""
    
    def __init__(self):
        # Create root window
        self.root = tk.Tk()
        self.root.title("PipeRec")
        self.root.geometry(f"{DIMENSIONS['window_width']}x{DIMENSIONS['window_height']}")
        self.root.configure(bg=COLORS['bg_dark'])
        self.root.resizable(False, False)
        
        # Prevent accidental close during recording
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Configure ttk styles
        self.style = ttk.Style()
        configure_ttk_styles(self.style)
        
        # Audio Engine
        self.capture = DualAudioCapture()
        self.processor = AudioProcessor()
        
        # Cleanup temp files from previous sessions
        self._cleanup_temp()
        
        # State
        self.recording = False
        self.cur_mic = None
        self.cur_monitor = None
        
        # Lock for thread safety
        self._lock = threading.Lock()
        self._closing = False
        
        # Build UI
        self._build_ui()
        self._init_audio()
        
        # Start update loop
        self._update_loop()
    
    def _build_ui(self):
        """Build the main user interface."""
        
        # Main container
        main = tk.Frame(self.root, bg=COLORS['bg_dark'])
        main.pack(fill='both', expand=True, padx=DIMENSIONS['padding_large'], 
                  pady=DIMENSIONS['padding_large'])
        
        # === Header ===
        header = tk.Frame(main, bg=COLORS['bg_dark'])
        header.pack(fill='x', pady=(0, DIMENSIONS['padding_medium']))
        
        title = tk.Label(
            header,
            text="PIPEREC",
            font=(FONTS['family'], FONTS['size_title'], 'bold'),
            fg=COLORS['text_primary'],
            bg=COLORS['bg_dark']
        )
        title.pack()
        
        subtitle = tk.Label(
            header,
            text="Gravador Profissional",
            font=(FONTS['family'], FONTS['size_small']),
            fg=COLORS['text_muted'],
            bg=COLORS['bg_dark']
        )
        subtitle.pack()
        
        # === VU Meters Card ===
        vu_card = tk.Frame(main, bg=COLORS['bg_card'], padx=10, pady=10)
        vu_card.pack(fill='x', pady=DIMENSIONS['padding_small'])
        
        self.vu_mic = VUMeterCanvas(vu_card, label="Microfone")
        self.vu_mic.pack(fill='x', pady=(0, 5))
        
        self.vu_sys = VUMeterCanvas(vu_card, label="Sistema")
        self.vu_sys.pack(fill='x')
        
        # === Timer ===
        timer_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        timer_frame.pack(pady=DIMENSIONS['padding_large'])
        
        self.timer = TimerDisplay(timer_frame)
        self.timer.pack()
        
        # === Control Buttons ===
        controls = tk.Frame(main, bg=COLORS['bg_dark'])
        controls.pack(pady=DIMENSIONS['padding_medium'])
        
        self.btn_record = RecordButton(controls, command=self._toggle_record)
        self.btn_record.pack(side='left', padx=10)
        
        self.btn_stop = StopButton(controls, command=self._stop_record)
        self.btn_stop.pack(side='left', padx=10)
        self.btn_stop.set_enabled(False)
        
        # === Device Selection ===
        devices_card = tk.Frame(main, bg=COLORS['bg_card'], padx=15, pady=15)
        devices_card.pack(fill='x', pady=DIMENSIONS['padding_medium'])
        
        self.sel_mic = DeviceDropdown(devices_card, "Microfone:", on_change=self._set_mic)
        self.sel_mic.pack(fill='x', pady=(0, 10))
        
        self.sel_mon = DeviceDropdown(devices_card, "Sistema (Loopback):", on_change=self._set_monitor)
        self.sel_mon.pack(fill='x')
        
        # === Status Bar ===
        self.status_bar = StatusBar(main)
        self.status_bar.pack(fill='x', side='bottom', pady=(DIMENSIONS['padding_medium'], 0))
    
    def _init_audio(self):
        """Initialize audio devices."""
        mics = list_microphone_devices()
        mons = list_monitor_devices()
        
        self.sel_mic.update_devices(mics)
        self.sel_mon.update_devices(mons)
        
        # Auto-select first devices
        if mics:
            self.cur_mic = mics[0]
        if mons:
            self.cur_monitor = mons[0]
        
        # Start monitoring
        if self.cur_mic and self.cur_monitor:
            self._start_monitoring()
    
    def _set_mic(self, device):
        """Set microphone device."""
        self.cur_mic = device
        self._start_monitoring()
    
    def _set_monitor(self, device):
        """Set monitor (loopback) device."""
        self.cur_monitor = device
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start audio monitoring for levels."""
        if self.cur_mic and self.cur_monitor:
            mic_pulse = self.cur_mic.get('pulse_name')
            mon_pulse = self.cur_monitor.get('pulse_name')
            self.capture.start_monitoring(mic_pulse, mon_pulse)
    
    def _toggle_record(self):
        """Start recording (button is disabled during recording)."""
        with self._lock:
            if not self.recording:
                self._start_record()
    
    def _start_record(self):
        """Start recording."""
        if self.capture.start_recording():
            self.recording = True
            self.btn_record.set_recording(True)
            self.btn_stop.set_enabled(True)
            self.timer.set_recording(True)
            self.status_bar.set_status("Gravando...", 'recording')
    
    def _stop_record(self):
        """Stop recording."""
        with self._lock:
            if not self.recording:
                return
            
            self.recording = False
            self.btn_record.set_recording(False)
            self.btn_stop.set_enabled(False)
            self.timer.set_recording(False)
            self.status_bar.set_status("Processando...", 'processing')
        
        # Process in background thread
        threading.Thread(target=self._finish_recording, daemon=True).start()
    
    def _finish_recording(self):
        """Finish and process recording (runs in thread)."""
        try:
            mic_wav, sys_wav = self.capture.stop_recording()
            
            if mic_wav and sys_wav:
                out = self.processor.process_recording(
                    mic_wav, sys_wav, "recordings", normalize=True
                )
                self.processor.cleanup_temp_files(mic_wav, sys_wav)
                
                # Update UI from main thread
                filename = os.path.basename(out)
                self.root.after(0, lambda: self.status_bar.set_status(
                    f"Salvo: {filename}", 'success'
                ))
            else:
                self.root.after(0, lambda: self.status_bar.set_status(
                    "Erro ao salvar gravação!", 'error'
                ))
        except Exception as e:
            print(f"Error processing: {e}")
            self.root.after(0, lambda: self.status_bar.set_status(
                f"Erro: {str(e)[:30]}", 'error'
            ))
    
    def _update_loop(self):
        """Main update loop for UI elements."""
        if self._closing:
            return
        
        try:
            # Update VU Meters
            if self.capture.is_monitoring:
                mic_level, sys_level = self.capture.get_levels()
                self.vu_mic.set_level(mic_level)
                self.vu_sys.set_level(sys_level)
            
            # Update Timer
            if self.recording:
                elapsed = int(time.time() - self.capture.start_time)
                self.timer.set_time(elapsed)
        except Exception as e:
            print(f"Update error: {e}")
        
        # Schedule next update
        self.root.after(ANIMATIONS['timer_update'], self._update_loop)
    
    def _on_close(self):
        """Handle window close request."""
        if self.recording:
            # Confirm before closing during recording
            if messagebox.askyesno(
                "Gravação em Andamento",
                "Uma gravação está em andamento.\n\n"
                "Deseja parar a gravação e salvar antes de sair?",
                icon='warning'
            ):
                self._stop_record()
                # Wait a bit for processing
                self.root.after(2000, self._do_close)
            else:
                return  # Don't close
        else:
            self._do_close()
    
    def _do_close(self):
        """Actually close the application."""
        self._closing = True
        self.capture.stop_monitoring()
        self._cleanup_temp()
        self.root.destroy()
    
    def _cleanup_temp(self):
        """Clean up temporary files."""
        try:
            # We assume temp dir is 'temp' relative to CWD, 
            # OR we can get it from self.capture.temp_dir if we want to be strict.
            # Default capture uses 'temp'.
            self.processor.cleanup_directory("temp")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def run(self):
        """Run the main application loop."""
        self.root.mainloop()


def main():
    app = PipeRecApp()
    app.run()


if __name__ == "__main__":
    main()
