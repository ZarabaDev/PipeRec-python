"""
PipeRec - Groq Transcription Client
Structured transcription using Whisper via Groq.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.transcription.models import (
    SpeakerSegment,
    TranscriptionMetadata,
    TranscriptionResult,
)

try:
    from groq import Groq
except ImportError:  # pragma: no cover - dependency is optional in local dev
    Groq = None


load_dotenv()


class GroqTranscriber:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "whisper-large-v3"

        try:
            self.timeout = float(os.getenv("GROQ_TIMEOUT", "120.0"))
        except ValueError:
            self.timeout = 120.0

        self.client = None

        if Groq is None:
            print("⚠️ Warning: groq package is not installed.")
            return

        if not self.api_key:
            print("⚠️ Warning: GROQ_API_KEY not found in environment variables.")
            return

        try:
            self.client = Groq(api_key=self.api_key, timeout=self.timeout)
        except Exception as exc:
            print(f"Error initializing Groq client: {exc}")
            self.client = None

    def available(self) -> bool:
        return self.client is not None

    def transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        if not self.client:
            return TranscriptionResult.failed(
                "groq",
                "Groq client not initialized.",
                audio_path=audio_path,
                model=self.model,
            )

        if not os.path.exists(audio_path):
            return TranscriptionResult.failed(
                "groq",
                f"Audio file not found: {audio_path}",
                audio_path=audio_path,
                model=self.model,
            )

        try:
            file_size = os.path.getsize(audio_path)
            if file_size > 25 * 1024 * 1024:
                print("⚠️ Warning: arquivo excede 25MB, a API Groq pode falhar.")
        except Exception as exc:
            print(f"Error checking file size: {exc}")

        try:
            print("🎙️ Transcribing with Groq (Whisper Large V3 structured)...")
            with open(audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model=self.model,
                    language="pt",
                    temperature=0.0,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            text = getattr(transcription, "text", "") or ""
            segments = self._extract_segments(transcription)
            metadata = TranscriptionMetadata(
                provider="groq",
                model=self.model,
                language=getattr(transcription, "language", None) or "pt",
                audio_path=audio_path,
                duration_seconds=self._as_float(getattr(transcription, "duration", None)),
                speaker_count=len({segment.speaker_id for segment in segments}) or 1,
                extra={
                    "segment_count": len(segments),
                },
            )
            return TranscriptionResult(
                status="completed",
                text=text.strip(),
                metadata=metadata,
                segments=segments,
                raw_response={
                    "language": getattr(transcription, "language", None),
                    "duration": getattr(transcription, "duration", None),
                },
            )
        except Exception as exc:
            print(f"Groq Transcription API Error: {exc}")
            return TranscriptionResult.failed(
                "groq",
                str(exc),
                audio_path=audio_path,
                model=self.model,
            )

    def _extract_segments(self, transcription: Any) -> list[SpeakerSegment]:
        raw_segments = getattr(transcription, "segments", None) or []
        segments: list[SpeakerSegment] = []

        for index, segment in enumerate(raw_segments):
            speaker_id = str(getattr(segment, "speaker", None) or 1)
            text = (getattr(segment, "text", "") or "").strip()
            segments.append(
                SpeakerSegment(
                    speaker_id=speaker_id,
                    text=text,
                    start_ms=self._seconds_to_ms(getattr(segment, "start", None)),
                    end_ms=self._seconds_to_ms(getattr(segment, "end", None)),
                    confidence=self._as_float(getattr(segment, "avg_logprob", None)),
                )
            )

        if segments:
            return segments

        text = (getattr(transcription, "text", "") or "").strip()
        if not text:
            return []

        return [
            SpeakerSegment(
                speaker_id="1",
                text=text,
                start_ms=0,
                end_ms=self._seconds_to_ms(getattr(transcription, "duration", None)),
            )
        ]

    @staticmethod
    def _seconds_to_ms(value: Any) -> int | None:
        numeric = GroqTranscriber._as_float(value)
        if numeric is None:
            return None
        return int(numeric * 1000)

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
