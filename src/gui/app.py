"""
PipeRec - Minimal Recording Console
Single-purpose home screen with protected recording flow.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.audio.capture import DualAudioCapture
from src.audio.devices import list_microphone_devices, list_monitor_devices
from src.audio.processor import AudioProcessor
from src.gui.components import (
    RecordButton,
    SettingsModal,
    SignalMeter,
    StopButton,
    TimerDisplay,
)
from src.gui.theme import COLORS, DIMENSIONS, FONTS, ANIMATIONS, configure_ttk_styles
from src.profiles.recording_profiles import ALL_PROFILES, REUNIAO_VISATION, RecordingProfile
from src.transcription.assemblyai_client import AssemblyAITranscriber
from src.transcription.exporters import (
    save_rich_transcript,
    save_text_transcript,
)
from src.transcription.groq_client import GroqTranscriber
from src.transcription.models import TranscriptionResult


class PipeRecApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PipeRec")
        self.root.geometry(f"{DIMENSIONS['window_width']}x{DIMENSIONS['window_height']}")
        self.root.minsize(420, 430)
        self.root.configure(bg=COLORS["bg_dark"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.style = ttk.Style()
        configure_ttk_styles(self.style)

        self.capture = DualAudioCapture()
        self.processor = AudioProcessor()
        self.assemblyai_transcriber = AssemblyAITranscriber()
        self.groq_transcriber = GroqTranscriber()

        self.active_profile: RecordingProfile = REUNIAO_VISATION
        self.recording = False
        self.cur_mic = None
        self.cur_monitor = None
        self._lock = threading.Lock()
        self._closing = False
        self._processing = False
        self._session_state = "idle"
        self._update_started = False
        self._latest_artifacts = {"text": None, "rich": None}

        self._cleanup_temp()
        self._build_ui()
        self._init_audio()
        self._set_session_state("idle")
        self._start_update_loop()

    def _build_ui(self):
        root_shell = tk.Frame(self.root, bg=COLORS["bg_dark"])
        root_shell.pack(fill="both", expand=True, padx=18, pady=18)

        top_bar = tk.Frame(root_shell, bg=COLORS["bg_dark"])
        top_bar.pack(fill="x", pady=(0, 14))

        tk.Label(
            top_bar,
            text="PipeRec",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            font=(FONTS["family"], FONTS["size_body"], "bold"),
        ).pack(side="left")

        self.profile_badge = tk.Label(
            top_bar,
            text=self.active_profile.nome,
            bg=COLORS["bg_shell_soft"],
            fg=COLORS["text_primary"],
            font=(FONTS["family"], FONTS["size_small"], "bold"),
            padx=10,
            pady=4,
        )
        self.profile_badge.pack(side="right")

        self.panel = tk.Frame(
            root_shell,
            bg=COLORS["bg_shell"],
            highlightthickness=1,
            highlightbackground=COLORS["border_soft"],
            padx=22,
            pady=22,
        )
        self.panel.pack(fill="both", expand=True)

        panel_header = tk.Frame(self.panel, bg=COLORS["bg_shell"])
        panel_header.pack(fill="x")

        self.state_badge = tk.Label(
            panel_header,
            text="Pronto",
            bg=COLORS["bg_shell_soft"],
            fg=COLORS["accent_success"],
            font=(FONTS["family"], FONTS["size_small"], "bold"),
            padx=10,
            pady=4,
        )
        self.state_badge.pack(side="left")

        self.config_button = tk.Button(
            panel_header,
            text="Config",
            command=self._open_settings,
            bg=COLORS["bg_shell_soft"],
            fg=COLORS["text_primary"],
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self.config_button.pack(side="right")

        self.status_line = tk.Label(
            self.panel,
            text=f"Pronto para gravar em {self.active_profile.nome}",
            bg=COLORS["bg_shell"],
            fg=COLORS["text_secondary"],
            font=(FONTS["family"], FONTS["size_body"]),
            anchor="w",
        )
        self.status_line.pack(fill="x", pady=(12, 4))

        self.timer = TimerDisplay(self.panel)
        self.timer.pack(pady=(6, 10))

        controls = tk.Frame(self.panel, bg=COLORS["bg_shell"])
        controls.pack(pady=(2, 18))

        self.btn_record = RecordButton(controls, command=self._toggle_record)
        self.btn_record.pack(side="left", padx=(0, 18))

        self.btn_stop = StopButton(controls, command=self._stop_record)
        self.btn_stop.pack(side="left")
        self.btn_stop.set_enabled(False)

        meters = tk.Frame(self.panel, bg=COLORS["bg_shell"])
        meters.pack(fill="x", pady=(8, 0))

        self.vu_mic = SignalMeter(meters, "Microfone")
        self.vu_mic.pack(fill="x", pady=(0, 10))

        self.vu_sys = SignalMeter(meters, "Sistema")
        self.vu_sys.pack(fill="x")

        self.settings_modal = SettingsModal(
            self.root,
            profiles=ALL_PROFILES,
            on_profile_change=self.set_active_profile,
            on_mic_change=self._set_mic,
            on_monitor_change=self._set_monitor,
            on_import_audio=self._import_audio,
        )
        self.settings_modal.update_profile(self.active_profile)

    def _init_audio(self):
        mics = list_microphone_devices()
        mons = list_monitor_devices()
        self.settings_modal.update_devices(mics, mons)

        if mics:
            self.cur_mic = mics[0]
        if mons:
            self.cur_monitor = mons[0]

        if self.cur_mic and self.cur_monitor:
            self._start_monitoring()

    def _start_update_loop(self):
        if not self._update_started:
            self._update_started = True
            self._update_loop()

    def _update_loop(self):
        if self._closing:
            return
        try:
            if self.capture.is_monitoring:
                mic_level, sys_level = self.capture.get_levels()
                self.vu_mic.set_level(mic_level)
                self.vu_sys.set_level(sys_level)
            if self.recording and self.capture.start_time:
                elapsed = int(time.time() - self.capture.start_time)
                self.timer.set_time(elapsed)
        except Exception as exc:
            print(f"Update error: {exc}")
        self.root.after(ANIMATIONS["timer_update"], self._update_loop)

    def _set_session_state(self, state: str):
        self._session_state = state
        self._processing = state == "processing_locked"
        locked = state in {"recording_locked", "processing_locked"}

        self.settings_modal.set_locked(locked)
        self.config_button.config(
            state="disabled" if locked else "normal",
            cursor="arrow" if locked else "hand2",
            bg=COLORS["bg_surface"] if locked else COLORS["bg_shell_soft"],
            fg=COLORS["text_muted"] if locked else COLORS["text_primary"],
        )

        if state == "recording_locked":
            self.state_badge.config(text="Gravando", fg=COLORS["accent_primary"])
            self.status_line.config(text="Gravação protegida. Controles críticos bloqueados.")
            self.timer.set_state("recording")
            self.btn_record.set_recording(True)
        elif state == "processing_locked":
            self.state_badge.config(text="Processando", fg=COLORS["accent_secondary"])
            self.status_line.config(text="Processando reunião. Aguarde desbloqueio.")
            self.timer.set_state("processing")
            self.btn_record.set_recording(True)
        elif state == "error_recovery":
            self.state_badge.config(text="Erro", fg=COLORS["accent_error"])
            self.status_line.config(text="Erro na última sessão. Toque REC para retomar com segurança.")
            self.timer.set_state("error")
            if not self.recording:
                self.btn_record.set_recording(False)
        else:
            self.state_badge.config(text="Pronto", fg=COLORS["accent_success"])
            self.status_line.config(text=f"Pronto para gravar em {self.active_profile.nome}")
            self.timer.set_state("idle")
            if not self.recording:
                self.btn_record.set_recording(False)

    def _open_settings(self):
        if self._session_state in {"recording_locked", "processing_locked"}:
            return
        self.settings_modal.show()

    def set_active_profile(self, profile: RecordingProfile):
        if self._session_state in {"recording_locked", "processing_locked"}:
            return
        self.active_profile = profile
        self.profile_badge.config(text=profile.nome)
        self.settings_modal.update_profile(profile)
        self.settings_modal.preview.clear()
        self.status_line.config(text=f"Pronto para gravar em {profile.nome}")

    def _set_mic(self, device):
        if self._session_state != "idle":
            return
        self.cur_mic = device
        self._start_monitoring()

    def _set_monitor(self, device):
        if self._session_state != "idle":
            return
        self.cur_monitor = device
        self._start_monitoring()

    def _start_monitoring(self):
        if self.cur_mic and self.cur_monitor:
            self.capture.start_monitoring(
                self.cur_mic.get("pulse_name"),
                self.cur_monitor.get("pulse_name"),
            )

    def _toggle_record(self):
        with self._lock:
            if self._session_state == "error_recovery":
                self._set_session_state("idle")
            if not self.recording:
                self._start_record()

    def _start_record(self):
        if self.capture.start_recording():
            self.recording = True
            self.btn_stop.set_enabled(True)
            self.settings_modal.hide()
            self.settings_modal.progress_panel.configure_for_profile(self.active_profile)
            self.settings_modal.progress_panel.set_status("Gravando sessão ativa", "recording")
            self._set_session_state("recording_locked")

    def _stop_record(self):
        with self._lock:
            if not self.recording:
                return
            self.recording = False
            self.btn_stop.set_enabled(False)
            self._set_session_state("processing_locked")
        threading.Thread(target=self._finish_recording, daemon=True).start()

    def _finish_recording(self):
        try:
            mic_wav, sys_wav = self.capture.stop_recording()
            if not (mic_wav and sys_wav):
                self.settings_modal.progress_panel.set_status("Erro ao salvar gravação", "error")
                self._set_session_state("error_recovery")
                return

            self.settings_modal.progress_panel.set_status("Processando áudio base", "processing")
            out = self.processor.process_recording(mic_wav, sys_wav, "recordings", normalize=True)
            transcription_audio = self.processor.process_for_transcription(mic_wav, sys_wav, "temp")
            self._process_audio_pipeline(transcription_audio, out)
            self.processor.cleanup_temp_files(mic_wav, sys_wav)
        except Exception as exc:
            print(f"Error finishing: {exc}")
            self.settings_modal.progress_panel.set_status(f"Erro: {str(exc)[:60]}", "error")
            self._set_session_state("error_recovery")

    def _import_audio(self):
        if self._session_state != "idle":
            return
        file_path = filedialog.askopenfilename(
            title="Selecionar áudio para transcrição",
            filetypes=[
                ("Arquivos de áudio", "*.mp3 *.wav *.m4a *.ogg *.flac"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not file_path:
            return
        self.settings_modal.hide()
        self.settings_modal.progress_panel.configure_for_profile(self.active_profile)
        self.settings_modal.progress_panel.set_status("Importando áudio", "processing")
        self._set_session_state("processing_locked")
        threading.Thread(
            target=self._process_audio_pipeline,
            args=(file_path,),
            daemon=True,
        ).start()

    def _process_audio_pipeline(
        self,
        audio_path: str,
        record_output_path: Optional[str] = None,
    ):
        try:
            transcription_result: TranscriptionResult | None = None
            transcription_failed = False
            base_output_path = record_output_path or audio_path

            if audio_path:
                self.settings_modal.progress_panel.set_step("transcricao", "active")
                provider_name, transcriber = self._select_transcriber()
                self.settings_modal.progress_panel.set_status(
                    f"Transcrevendo com {provider_name}",
                    "processing",
                )
                transcription_result = transcriber.transcribe_audio(audio_path)
                if not transcription_result.ok:
                    fallback = self._transcribe_with_fallback(audio_path, provider_name)
                    if fallback is not None:
                        transcription_result = fallback

                transcription_failed = not transcription_result.ok
                self.settings_modal.progress_panel.set_step(
                    "transcricao",
                    "error" if transcription_failed else "done",
                )

                if not transcription_failed and transcription_result is not None:
                    self.settings_modal.progress_panel.set_step("estrutura", "active")
                    self.settings_modal.progress_panel.set_status("Persistindo artefatos", "processing")
                    text_path = str(save_text_transcript(base_output_path, transcription_result))
                    rich_path = None
                    if self.active_profile.export_rich_transcript:
                        rich_path = str(save_rich_transcript(base_output_path, transcription_result))
                    self._latest_artifacts["text"] = text_path
                    self._latest_artifacts["rich"] = rich_path
                    self.settings_modal.update_artifacts(self._latest_artifacts)
                    self.settings_modal.progress_panel.set_step("estrutura", "done")
                else:
                    self.settings_modal.progress_panel.set_step("estrutura", "error")
                self._cleanup_transcription_temp(audio_path)

            if transcription_failed:
                self.settings_modal.progress_panel.set_status("Erro na transcrição", "error")
                self._set_session_state("error_recovery")
            else:
                self.settings_modal.progress_panel.set_status("Transcrição concluída", "success")
                if transcription_result and transcription_result.text:
                    lines = [
                        segment.render_line(include_timestamps=True)
                        for segment in transcription_result.segments[:8]
                    ]
                    self.settings_modal.preview.set_segments_preview(lines, transcription_result.metadata.speaker_count)
                self._set_session_state("idle")
        except Exception as exc:
            print(f"Error in pipeline: {exc}")
            self.settings_modal.progress_panel.set_status(f"Erro crítico: {str(exc)[:60]}", "error")
            self._set_session_state("error_recovery")

    def _select_transcriber(self):
        provider = self.active_profile.transcription_provider
        if provider == "assemblyai" and self.assemblyai_transcriber.available():
            return "AssemblyAI", self.assemblyai_transcriber
        return "Groq", self.groq_transcriber

    def _transcribe_with_fallback(self, audio_path: str, primary_provider_name: str):
        fallback_provider = self.active_profile.fallback_provider
        if fallback_provider == "groq" and primary_provider_name != "Groq" and self.groq_transcriber.available():
            self.settings_modal.progress_panel.set_status("Fallback para Groq", "warning")
            fallback_result = self.groq_transcriber.transcribe_audio(audio_path)
            if fallback_result.ok:
                return fallback_result
        return None

    def _cleanup_transcription_temp(self, audio_path: str):
        if os.path.basename(audio_path).startswith("transcription_"):
            try:
                os.remove(audio_path)
            except OSError:
                pass

    def _cleanup_temp(self):
        try:
            self.processor.cleanup_directory("temp")
        except Exception as exc:
            print(f"Cleanup error: {exc}")

    def _on_close(self):
        if self.recording:
            if messagebox.askyesno(
                "Gravação em andamento",
                "Há uma gravação protegida em andamento.\n\nDeseja parar, salvar o que foi capturado e encerrar após o processamento?",
                icon="warning",
            ):
                self._stop_record()
                self.root.after(2000, self._do_close)
            return
        self._do_close()

    def _do_close(self):
        self._closing = True
        self.capture.stop_monitoring()
        self._cleanup_temp()
        self.settings_modal.hide()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = PipeRecApp()
    app.run()


if __name__ == "__main__":
    main()
