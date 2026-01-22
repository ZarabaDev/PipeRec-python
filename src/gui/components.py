"""
PipeRec - Professional GUI Components (Pure Tkinter)
Custom widgets: VU Meter, Timer Display, Control Buttons.
"""

import tkinter as tk
from tkinter import ttk
from .theme import COLORS, FONTS, DIMENSIONS, ANIMATIONS


class VUMeterCanvas(tk.Canvas):
    """
    Professional VU Meter with segmented LED-style display.
    """
    
    def __init__(self, parent, label: str = "Audio", **kwargs):
        self.height = DIMENSIONS['vu_height']
        self.segments = DIMENSIONS['vu_segments']
        self.segment_gap = 2
        
        super().__init__(
            parent,
            height=self.height + 20,
            bg=COLORS['bg_card'],
            highlightthickness=0,
            **kwargs
        )
        
        self.label = label
        self.level = 0.0  # 0.0 to 1.0
        self._segment_ids = []
        
        self.bind('<Configure>', self._on_resize)
        
    def _on_resize(self, event=None):
        self.delete('all')
        self._segment_ids = []
        
        width = self.winfo_width()
        if width < 50:
            return
            
        # Label
        self.create_text(
            10, self.height // 2 + 10,
            text=self.label,
            fill=COLORS['text_secondary'],
            font=(FONTS['family'], FONTS['size_small']),
            anchor='w'
        )
        
        # Calculate segment dimensions
        label_offset = 80
        available = width - label_offset - 10
        seg_width = (available - (self.segments - 1) * self.segment_gap) / self.segments
        
        for i in range(self.segments):
            x1 = label_offset + i * (seg_width + self.segment_gap)
            x2 = x1 + seg_width
            y1 = 8
            y2 = self.height + 8
            
            rect_id = self.create_rectangle(
                x1, y1, x2, y2,
                fill=COLORS['vu_bg'],
                outline='',
                tags=f'seg_{i}'
            )
            self._segment_ids.append(rect_id)
        
        self._update_display()
    
    def set_level(self, level_db: float):
        """Set level in dB (-100 to 0)."""
        # Convert dB to 0-1 range
        # -60 dB = 0.0, 0 dB = 1.0
        normalized = max(0, min(1, (level_db + 60) / 60))
        self.level = normalized
        self._update_display()
    
    def _update_display(self):
        if not self._segment_ids:
            return
            
        active_segments = int(self.level * self.segments)
        
        for i, seg_id in enumerate(self._segment_ids):
            if i < active_segments:
                # Determine color based on position
                ratio = i / self.segments
                if ratio < 0.6:
                    color = COLORS['vu_low']
                elif ratio < 0.85:
                    color = COLORS['vu_mid']
                else:
                    color = COLORS['vu_high']
            else:
                color = COLORS['vu_bg']
                
            self.itemconfig(seg_id, fill=color)


class TimerDisplay(tk.Canvas):
    """
    Large LED-style timer display.
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            width=200,
            height=70,
            bg=COLORS['bg_dark'],
            highlightthickness=0,
            **kwargs
        )
        
        self._text_id = self.create_text(
            100, 35,
            text="00:00",
            fill=COLORS['text_primary'],
            font=(FONTS['family_mono'], FONTS['size_timer'], 'bold')
        )
        
        self._recording = False
        
    def set_time(self, seconds: int):
        mins, secs = divmod(seconds, 60)
        self.itemconfig(self._text_id, text=f"{mins:02d}:{secs:02d}")
    
    def set_recording(self, is_recording: bool):
        self._recording = is_recording
        if is_recording:
            self.itemconfig(self._text_id, fill=COLORS['accent_primary'])
        else:
            self.itemconfig(self._text_id, fill=COLORS['text_primary'])
            self.set_time(0)


class RecordButton(tk.Canvas):
    """
    Large circular record button with pulsing animation.
    """
    
    def __init__(self, parent, command=None, **kwargs):
        self.size = 100
        super().__init__(
            parent,
            width=self.size,
            height=self.size,
            bg=COLORS['bg_dark'],
            highlightthickness=0,
            cursor='hand2',
            **kwargs
        )
        
        self.command = command
        self._recording = False
        self._enabled = True
        self._pulse_phase = 0
        self._pulse_job = None
        
        # Draw button
        self._outer = self.create_oval(
            5, 5, self.size - 5, self.size - 5,
            fill=COLORS['bg_elevated'],
            outline=COLORS['border'],
            width=2
        )
        
        self._inner = self.create_oval(
            20, 20, self.size - 20, self.size - 20,
            fill=COLORS['accent_primary'],
            outline=''
        )
        
        self._text = self.create_text(
            self.size // 2, self.size // 2,
            text="REC",
            fill=COLORS['text_primary'],
            font=(FONTS['family'], 14, 'bold')
        )
        
        # Bindings
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_click(self, event):
        if self._enabled and self.command:
            self.command()
    
    def _on_enter(self, event):
        if not self._recording:
            self.itemconfig(self._outer, fill=COLORS['bg_hover'])
    
    def _on_leave(self, event):
        if not self._recording:
            self.itemconfig(self._outer, fill=COLORS['bg_elevated'])
    
    def set_recording(self, is_recording: bool):
        self._recording = is_recording
        self._enabled = not is_recording  # Disable when recording
        
        if is_recording:
            # Show disabled state - grayed out
            self.itemconfig(self._text, text="REC")
            self.itemconfig(self._inner, fill=COLORS['text_muted'])
            self.itemconfig(self._outer, fill=COLORS['bg_surface'])
            self.config(cursor='arrow')
        else:
            self.itemconfig(self._text, text="REC")
            self.itemconfig(self._inner, fill=COLORS['accent_primary'])
            self.itemconfig(self._outer, fill=COLORS['bg_elevated'])
            self.config(cursor='hand2')
            self._stop_pulse()
    
    def _start_pulse(self):
        self._pulse_phase = 0
        self._do_pulse()
    
    def _stop_pulse(self):
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
        self.itemconfig(self._outer, outline=COLORS['border'], width=2)
    
    def _do_pulse(self):
        if not self._recording:
            return
            
        # Pulse effect on outer ring
        self._pulse_phase = (self._pulse_phase + 1) % 20
        
        if self._pulse_phase < 10:
            width = 2 + self._pulse_phase * 0.3
            self.itemconfig(self._outer, outline=COLORS['accent_primary'], width=width)
        else:
            width = 5 - (self._pulse_phase - 10) * 0.3
            self.itemconfig(self._outer, outline=COLORS['accent_primary'], width=max(2, width))
        
        self._pulse_job = self.after(ANIMATIONS['pulse_speed'] // 20, self._do_pulse)


class StopButton(tk.Canvas):
    """
    Stop button - square icon.
    """
    
    def __init__(self, parent, command=None, **kwargs):
        self.size = 60
        super().__init__(
            parent,
            width=self.size,
            height=self.size,
            bg=COLORS['bg_dark'],
            highlightthickness=0,
            cursor='hand2',
            **kwargs
        )
        
        self.command = command
        self._enabled = False
        
        # Draw button
        self._outer = self.create_oval(
            3, 3, self.size - 3, self.size - 3,
            fill=COLORS['bg_surface'],
            outline=COLORS['border'],
            width=1
        )
        
        # Square stop icon
        pad = 18
        self._inner = self.create_rectangle(
            pad, pad, self.size - pad, self.size - pad,
            fill=COLORS['text_muted'],
            outline=''
        )
        
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_click(self, event):
        if self._enabled and self.command:
            self.command()
    
    def _on_enter(self, event):
        if self._enabled:
            self.itemconfig(self._outer, fill=COLORS['bg_hover'])
    
    def _on_leave(self, event):
        self.itemconfig(self._outer, fill=COLORS['bg_surface'] if not self._enabled else COLORS['bg_elevated'])
    
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self.itemconfig(self._inner, fill=COLORS['accent_error'])
            self.itemconfig(self._outer, fill=COLORS['bg_elevated'])
            self.config(cursor='hand2')
        else:
            self.itemconfig(self._inner, fill=COLORS['text_muted'])
            self.itemconfig(self._outer, fill=COLORS['bg_surface'])
            self.config(cursor='arrow')


class DeviceDropdown(ttk.Frame):
    """
    Styled device selector dropdown.
    """
    
    def __init__(self, parent, label: str, on_change=None, **kwargs):
        super().__init__(parent, style='Card.TFrame', **kwargs)
        
        self.on_change = on_change
        self.devices = []
        
        # Label
        lbl = ttk.Label(self, text=label, style='Card.TLabel')
        lbl.pack(anchor='w', pady=(0, 4))
        
        # Combobox
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(
            self,
            textvariable=self.var,
            state='readonly',
            width=35
        )
        self.combo.pack(fill='x')
        self.combo.bind('<<ComboboxSelected>>', self._on_select)
    
    def _on_select(self, event):
        name = self.var.get()
        for d in self.devices:
            if d['name'] == name:
                if self.on_change:
                    self.on_change(d)
                break
    
    def update_devices(self, devices: list):
        self.devices = devices
        names = [d['name'] for d in devices] if devices else ["Nenhum dispositivo"]
        self.combo['values'] = names
        if names:
            self.var.set(names[0])


class StatusBar(ttk.Frame):
    """
    Status bar at bottom of window.
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='Surface.TFrame', **kwargs)
        
        self._indicator = tk.Canvas(
            self, width=10, height=10,
            bg=COLORS['bg_surface'],
            highlightthickness=0
        )
        self._indicator.pack(side='left', padx=(10, 5), pady=8)
        self._dot = self._indicator.create_oval(2, 2, 8, 8, fill=COLORS['text_muted'], outline='')
        
        self._label = ttk.Label(self, text="Pronto para gravar", style='Status.TLabel')
        self._label.pack(side='left', pady=8)
        self._label.configure(background=COLORS['bg_surface'])
    
    def set_status(self, text: str, state: str = 'idle'):
        self._label.configure(text=text)
        
        colors = {
            'idle': COLORS['text_muted'],
            'recording': COLORS['accent_primary'],
            'processing': COLORS['accent_warning'],
            'success': COLORS['accent_success'],
            'error': COLORS['accent_error']
        }
        
        self._indicator.itemconfig(self._dot, fill=colors.get(state, COLORS['text_muted']))
