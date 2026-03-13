"""
PipeRec - Minimalist GUI Components
Focused recording surface plus configuration modal.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .theme import ANIMATIONS, COLORS, DIMENSIONS, FONTS


class TimerDisplay(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            width=280,
            height=92,
            bg=COLORS["bg_dark"],
            highlightthickness=0,
            **kwargs,
        )
        self._text_id = self.create_text(
            140,
            46,
            text="00:00",
            fill=COLORS["text_primary"],
            font=(FONTS["family_mono"], FONTS["size_timer"], "bold"),
        )

    def set_time(self, seconds: int):
        mins, secs = divmod(max(0, seconds), 60)
        self.itemconfig(self._text_id, text=f"{mins:02d}:{secs:02d}")

    def set_state(self, state: str):
        color = COLORS["text_primary"]
        if state == "recording":
            color = COLORS["accent_primary"]
        elif state == "processing":
            color = COLORS["accent_secondary"]
        elif state == "error":
            color = COLORS["accent_error"]
        self.itemconfig(self._text_id, fill=color)


class RecordButton(tk.Canvas):
    def __init__(self, parent, command=None, **kwargs):
        self.size = 112
        super().__init__(
            parent,
            width=self.size,
            height=self.size,
            bg=COLORS["bg_dark"],
            highlightthickness=0,
            cursor="hand2",
            **kwargs,
        )
        self.command = command
        self._enabled = True
        self._pulse_job = None
        self._pulse_phase = 0

        self._halo = self.create_oval(
            4, 4, self.size - 4, self.size - 4,
            fill=COLORS["bg_shell_soft"],
            outline=COLORS["border_soft"],
            width=2,
        )
        self._core = self.create_oval(
            21, 21, self.size - 21, self.size - 21,
            fill=COLORS["accent_primary"],
            outline="",
        )
        self._text = self.create_text(
            self.size // 2,
            self.size // 2,
            text="REC",
            fill=COLORS["text_primary"],
            font=(FONTS["family"], 15, "bold"),
        )

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_click(self, event):
        if self._enabled and self.command:
            self.command()

    def _on_enter(self, event):
        if self._enabled:
            self.itemconfig(self._halo, fill=COLORS["bg_hover"])

    def _on_leave(self, event):
        if self._enabled:
            self.itemconfig(self._halo, fill=COLORS["bg_shell_soft"])

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.config(cursor="hand2" if enabled else "arrow")
        if enabled:
            self.itemconfig(self._core, fill=COLORS["accent_primary"])
            self.itemconfig(self._text, fill=COLORS["text_primary"])
            self.itemconfig(self._halo, fill=COLORS["bg_shell_soft"])
        else:
            self.itemconfig(self._core, fill=COLORS["text_muted"])
            self.itemconfig(self._text, fill=COLORS["bg_dark"])
            self.itemconfig(self._halo, fill=COLORS["bg_surface"])
            self._stop_pulse()

    def set_recording(self, is_recording: bool):
        if is_recording:
            self.set_enabled(False)
            self._start_pulse()
        else:
            self._stop_pulse()
            self.set_enabled(True)

    def _start_pulse(self):
        self._pulse_phase = 0
        self._do_pulse()

    def _stop_pulse(self):
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
        self.itemconfig(self._halo, outline=COLORS["border_soft"], width=2)

    def _do_pulse(self):
        width = 2 + (self._pulse_phase % 8) * 0.45
        self.itemconfig(self._halo, outline=COLORS["accent_primary"], width=width)
        self._pulse_phase += 1
        self._pulse_job = self.after(ANIMATIONS["pulse_speed"] // 16, self._do_pulse)


class StopButton(tk.Canvas):
    def __init__(self, parent, command=None, **kwargs):
        self.size = 76
        super().__init__(
            parent,
            width=self.size,
            height=self.size,
            bg=COLORS["bg_dark"],
            highlightthickness=0,
            cursor="arrow",
            **kwargs,
        )
        self.command = command
        self._enabled = False

        self._shell = self.create_oval(
            3, 3, self.size - 3, self.size - 3,
            fill=COLORS["bg_surface"],
            outline=COLORS["border_soft"],
            width=1,
        )
        pad = 24
        self._square = self.create_rectangle(
            pad, pad, self.size - pad, self.size - pad,
            fill=COLORS["text_muted"],
            outline="",
        )

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_click(self, event):
        if self._enabled and self.command:
            self.command()

    def _on_enter(self, event):
        if self._enabled:
            self.itemconfig(self._shell, fill=COLORS["bg_hover"])

    def _on_leave(self, event):
        self.itemconfig(
            self._shell,
            fill=COLORS["bg_shell_soft"] if self._enabled else COLORS["bg_surface"],
        )

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.config(cursor="hand2" if enabled else "arrow")
        self.itemconfig(
            self._square,
            fill=COLORS["accent_error"] if enabled else COLORS["text_muted"],
        )
        self.itemconfig(
            self._shell,
            fill=COLORS["bg_shell_soft"] if enabled else COLORS["bg_surface"],
        )


class SignalMeter(tk.Canvas):
    def __init__(self, parent, label: str, **kwargs):
        self.label = label
        self.level = 0.0
        self.segments = 16
        super().__init__(
            parent,
            height=36,
            bg=COLORS["bg_shell"],
            highlightthickness=0,
            **kwargs,
        )
        self.bind("<Configure>", self._draw)

    def set_level(self, level_db: float):
        self.level = max(0, min(1, (level_db + 60) / 60))
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        width = self.winfo_width()
        if width <= 40:
            return

        self.create_text(
            12,
            18,
            text=self.label,
            fill=COLORS["text_secondary"],
            font=(FONTS["family"], FONTS["size_small"]),
            anchor="w",
        )
        self.create_oval(86, 12, 94, 20, fill=COLORS["accent_success"], outline="")

        bar_start = 108
        bar_width = max(80, width - bar_start - 12)
        seg_w = max(4, (bar_width - (self.segments - 1) * 4) / self.segments)
        active = int(self.level * self.segments)

        for idx in range(self.segments):
            x1 = bar_start + idx * (seg_w + 4)
            x2 = x1 + seg_w
            color = COLORS["meter_off"]
            if idx < active:
                color = COLORS["accent_primary"] if idx > self.segments * 0.75 else COLORS["meter_on"]
            self.create_rectangle(x1, 11, x2, 25, fill=color, outline="")


class LockedComboboxFrame(ttk.Frame):
    def __init__(self, parent, label: str, on_change=None, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self.on_change = on_change
        self._locked = False
        self._items = []

        ttk.Label(self, text=label, style="Card.TLabel").pack(anchor="w", pady=(0, 4))
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.var, state="readonly")
        self.combo.pack(fill="x")
        self.combo.bind("<<ComboboxSelected>>", self._on_select)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>", "<KeyPress>"):
            self.combo.bind(seq, self._block_when_locked, add="+")

    def _block_when_locked(self, event):
        if self._locked:
            return "break"

    def _on_select(self, event):
        if self._locked:
            return "break"
        selected = self.var.get()
        for item in self._items:
            if item["name"] == selected and self.on_change:
                self.on_change(item)
                break

    def update_items(self, items: list[dict]):
        self._items = items
        names = [item["name"] for item in items] or ["Nenhum dispositivo"]
        self.combo["values"] = names
        if names:
            self.var.set(names[0])

    def set_locked(self, locked: bool):
        self._locked = locked
        self.combo.config(state="disabled" if locked else "readonly")


class DeviceDropdown(LockedComboboxFrame):
    def update_devices(self, devices: list[dict]):
        self.update_items(devices)


class ProfileSelector(LockedComboboxFrame):
    def __init__(self, parent, profiles: list, on_change=None, **kwargs):
        self.profiles = profiles
        super().__init__(parent, "Perfil de Gravação", on_change=on_change, **kwargs)
        self.combo["values"] = [profile.nome for profile in profiles]
        if profiles:
            self.var.set(profiles[0].nome)

    def _on_select(self, event):
        if self._locked:
            return "break"
        for profile in self.profiles:
            if profile.nome == self.var.get() and self.on_change:
                self.on_change(profile)
                break

    def set_profile(self, profile):
        self.var.set(profile.nome)


class ProgressPanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="Surface.TFrame", **kwargs)
        self.steps_config = [
            {"key": "transcricao", "label": "Transcrevendo"},
            {"key": "estrutura", "label": "Estruturando"},
        ]
        self.steps_ui = {}

        self.summary = tk.Label(
            self,
            text="Pronto para gravação",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_secondary"],
            font=(FONTS["family"], FONTS["size_body"]),
            anchor="w",
        )
        self.summary.pack(fill="x", padx=12, pady=(10, 6))

        self.steps_frame = tk.Frame(self, bg=COLORS["bg_surface"])
        self.steps_frame.pack(fill="x", padx=12, pady=(0, 12))

        for step in self.steps_config:
            frame = tk.Frame(self.steps_frame, bg=COLORS["bg_surface"])
            frame.pack(fill="x", pady=2)
            dot = tk.Canvas(frame, width=10, height=10, bg=COLORS["bg_surface"], highlightthickness=0)
            dot.pack(side="left", padx=(0, 8))
            oval = dot.create_oval(2, 2, 8, 8, fill=COLORS["text_muted"], outline="")
            label = tk.Label(
                frame,
                text=step["label"],
                bg=COLORS["bg_surface"],
                fg=COLORS["text_secondary"],
                font=(FONTS["family"], FONTS["size_small"]),
                anchor="w",
            )
            label.pack(side="left")
            self.steps_ui[step["key"]] = {"dot": dot, "oval": oval, "label": label}

    def configure_for_profile(self, profile):
        self.reset()

    def reset(self):
        for step in self.steps_ui:
            self.set_step(step, "idle")
        self.set_status("Pronto para gravação")

    def set_step(self, key: str, state: str):
        if key not in self.steps_ui:
            return
        colors = {
            "idle": (COLORS["text_muted"], COLORS["text_secondary"]),
            "active": (COLORS["accent_secondary"], COLORS["text_primary"]),
            "done": (COLORS["accent_success"], COLORS["accent_success"]),
            "error": (COLORS["accent_error"], COLORS["accent_error"]),
            "skip": (COLORS["border_soft"], COLORS["text_muted"]),
        }
        dot_color, text_color = colors.get(state, colors["idle"])
        self.steps_ui[key]["dot"].itemconfig(self.steps_ui[key]["oval"], fill=dot_color)
        self.steps_ui[key]["label"].config(fg=text_color)

    def set_status(self, text: str, state: str = "idle"):
        colors = {
            "idle": COLORS["text_secondary"],
            "recording": COLORS["accent_warning"],
            "processing": COLORS["accent_secondary"],
            "success": COLORS["accent_success"],
            "error": COLORS["accent_error"],
            "warning": COLORS["accent_warning"],
        }
        self.summary.config(text=text, fg=colors.get(state, COLORS["text_secondary"]))


class TranscriptionPreview(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)
        header = tk.Frame(self, bg=COLORS["bg_card"])
        header.pack(fill="x", pady=(0, 6))
        tk.Label(
            header,
            text="Prévia da transcrição",
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            font=(FONTS["family"], FONTS["size_small"], "bold"),
        ).pack(side="left")
        self.meta = tk.Label(
            header,
            text="",
            bg=COLORS["bg_card"],
            fg=COLORS["accent_secondary"],
            font=(FONTS["family"], FONTS["size_small"]),
        )
        self.meta.pack(side="right")

        self.text = tk.Text(
            self,
            height=8,
            bg=COLORS["bg_elevated"],
            fg=COLORS["text_primary"],
            font=(FONTS["family"], FONTS["size_small"]),
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border_soft"],
            wrap="word",
            state="disabled",
        )
        self.text.pack(fill="both", expand=True)

    def clear(self):
        self.meta.config(text="")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    def set_preview(self, text: str, speaker: str | None = None):
        preview = text[:600] + ("..." if len(text) > 600 else "")
        self.meta.config(text=speaker or "")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", preview)
        self.text.config(state="disabled")

    def set_segments_preview(self, lines: list[str], speaker_count: int | None = None):
        self.set_preview("\n".join(lines[:8]), speaker=f"{speaker_count or 0} locutores")


class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=COLORS["bg_card"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS["bg_card"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags="frame")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig("frame", width=e.width))


class SettingsModal:
    def __init__(
        self,
        parent,
        *,
        profiles: list,
        on_profile_change,
        on_mic_change,
        on_monitor_change,
        on_import_audio,
    ):
        self.window = tk.Toplevel(parent)
        self.window.title("Configuração")
        self.window.configure(bg=COLORS["bg_card"])
        self.window.geometry("480x560")
        self.window.minsize(420, 480)
        self.window.withdraw()
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        shell = tk.Frame(self.window, bg=COLORS["bg_card"], padx=14, pady=14)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=COLORS["bg_card"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(
            header,
            text="Configurações e detalhes",
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            font=(FONTS["family"], FONTS["size_heading"], "bold"),
        ).pack(side="left")
        tk.Button(
            header,
            text="Fechar",
            command=self.hide,
            bg=COLORS["bg_shell_soft"],
            fg=COLORS["text_primary"],
            relief="flat",
            padx=10,
            pady=4,
        ).pack(side="right")

        self.note = tk.Label(
            shell,
            text="Configurações disponíveis apenas fora da gravação.",
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            font=(FONTS["family"], FONTS["size_small"]),
            anchor="w",
        )
        self.note.pack(fill="x", pady=(0, 10))

        scroll = ScrollableFrame(shell)
        scroll.pack(fill="both", expand=True)
        body = scroll.scrollable_frame
        body.config(padx=2, pady=2)

        config_card = tk.Frame(body, bg=COLORS["bg_shell"], padx=12, pady=12)
        config_card.pack(fill="x", pady=(0, 12))
        tk.Label(
            config_card,
            text="Configuração",
            bg=COLORS["bg_shell"],
            fg=COLORS["text_primary"],
            font=(FONTS["family"], FONTS["size_body"], "bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.profile_selector = ProfileSelector(config_card, profiles=profiles, on_change=on_profile_change)
        self.profile_selector.pack(fill="x", pady=(0, 8))
        self.mic_selector = DeviceDropdown(config_card, "Microfone", on_change=on_mic_change)
        self.mic_selector.pack(fill="x", pady=(0, 8))
        self.monitor_selector = DeviceDropdown(config_card, "Sistema", on_change=on_monitor_change)
        self.monitor_selector.pack(fill="x", pady=(0, 10))

        self.import_button = tk.Button(
            config_card,
            text="Importar áudio",
            command=on_import_audio,
            bg=COLORS["accent_secondary"],
            fg=COLORS["text_primary"],
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
        )
        self.import_button.pack(anchor="w")

        details_card = tk.Frame(body, bg=COLORS["bg_shell"], padx=12, pady=12)
        details_card.pack(fill="both", expand=True)
        tk.Label(
            details_card,
            text="Detalhes",
            bg=COLORS["bg_shell"],
            fg=COLORS["text_primary"],
            font=(FONTS["family"], FONTS["size_body"], "bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.progress_panel = ProgressPanel(details_card)
        self.progress_panel.pack(fill="x", pady=(0, 10))

        self.preview = TranscriptionPreview(details_card, padx=10, pady=10)
        self.preview.pack(fill="both", expand=True, pady=(0, 10))

        artifact_card = tk.Frame(details_card, bg=COLORS["bg_card"], padx=10, pady=10)
        artifact_card.pack(fill="x")
        tk.Label(
            artifact_card,
            text="Últimos artefatos",
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            font=(FONTS["family"], FONTS["size_small"], "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.artifact_labels = {}
        for key, title in (("text", "TXT"), ("rich", "RICH")):
            row = tk.Frame(artifact_card, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(
                row,
                text=f"{title}:",
                width=6,
                anchor="w",
                bg=COLORS["bg_card"],
                fg=COLORS["text_muted"],
                font=(FONTS["family"], FONTS["size_small"]),
            ).pack(side="left")
            label = tk.Label(
                row,
                text="-",
                anchor="w",
                bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"],
                font=(FONTS["family_mono"], FONTS["size_small"]),
            )
            label.pack(side="left", fill="x", expand=True)
            self.artifact_labels[key] = label

    def show(self):
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def hide(self):
        self.window.withdraw()

    def set_locked(self, locked: bool):
        self.profile_selector.set_locked(locked)
        self.mic_selector.set_locked(locked)
        self.monitor_selector.set_locked(locked)
        self.import_button.config(
            state="disabled" if locked else "normal",
            cursor="arrow" if locked else "hand2",
        )

    def update_devices(self, microphones: list[dict], monitors: list[dict]):
        self.mic_selector.update_devices(microphones)
        self.monitor_selector.update_devices(monitors)

    def update_profile(self, profile):
        self.profile_selector.set_profile(profile)
        self.progress_panel.configure_for_profile(profile)

    def update_artifacts(self, artifacts: dict[str, str | None]):
        for key, label in self.artifact_labels.items():
            value = artifacts.get(key)
            label.config(text=value.split("/")[-1] if value else "-")
