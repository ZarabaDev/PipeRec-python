"""
PipeRec - AssemblyAI Transcription Client
Structured transcription with diarization and speaker segments.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.transcription.models import (
    SpeakerSegment,
    TranscriptionMetadata,
    TranscriptionResult,
    WordTiming,
)

try:
    import assemblyai as aai
except ImportError:  # pragma: no cover - dependency is optional in local dev
    aai = None


load_dotenv()


class AssemblyAITranscriber:
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.model = "universal-3-pro"
        self.fallback_models = [self.model, "universal-2"]
        self.client = None

        if aai is None:
            print("⚠️ Warning: assemblyai package is not installed.")
            return

        if not self.api_key:
            print("⚠️ Warning: ASSEMBLYAI_API_KEY not found in environment variables.")
            return

        try:
            aai.settings.api_key = self.api_key
            timeout = float(os.getenv("ASSEMBLYAI_TIMEOUT", 3600))
            aai.settings.http_timeout = timeout
            self.client = aai.Transcriber()
        except Exception as exc:
            print(f"Error initializing AssemblyAI client: {exc}")
            self.client = None

    def available(self) -> bool:
        return self.client is not None

    def transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        if not self.client:
            return TranscriptionResult.failed(
                "assemblyai",
                "AssemblyAI client not initialized.",
                audio_path=audio_path,
                model=self.model,
            )

        if not os.path.exists(audio_path):
            return TranscriptionResult.failed(
                "assemblyai",
                f"Audio file not found: {audio_path}",
                audio_path=audio_path,
                model=self.model,
            )

        try:
            print("🎙️ Transcribing with AssemblyAI (structured diarization)...")
            config = aai.TranscriptionConfig(
                speaker_labels=True,
                language_detection=True,
                speech_models=self.fallback_models,
            )
            transcript = self.client.transcribe(audio_path, config=config)

            if transcript.status == aai.TranscriptStatus.error:
                return TranscriptionResult.failed(
                    "assemblyai",
                    transcript.error or "Unknown AssemblyAI transcription error.",
                    audio_path=audio_path,
                    model=self.model,
                )

            segments = self._extract_segments(transcript)
            text = getattr(transcript, "text", "") or "\n".join(
                segment.render_line(include_timestamps=False) for segment in segments
            )

            metadata = TranscriptionMetadata(
                provider="assemblyai",
                model=getattr(transcript, "speech_model", None) or self.model,
                language=getattr(transcript, "language_code", None)
                or getattr(transcript, "language", None),
                audio_path=audio_path,
                duration_seconds=self._extract_duration_seconds(transcript),
                speaker_count=len({segment.speaker_id for segment in segments}) or None,
                extra={
                    "audio_duration": getattr(transcript, "audio_duration", None),
                    "utterance_count": len(segments),
                },
            )
            return TranscriptionResult(
                status="completed",
                text=text.strip(),
                metadata=metadata,
                segments=segments,
                confidence=self._extract_confidence(transcript, segments),
                raw_response=self._build_raw_response_snapshot(transcript),
            )
        except Exception as exc:
            print(f"AssemblyAI Transcription API Error: {exc}")
            return TranscriptionResult.failed(
                "assemblyai",
                str(exc),
                audio_path=audio_path,
                model=self.model,
            )

    def _extract_segments(self, transcript: Any) -> list[SpeakerSegment]:
        utterances = getattr(transcript, "utterances", None) or []
        segments: list[SpeakerSegment] = []

        for index, utterance in enumerate(utterances):
            speaker = str(getattr(utterance, "speaker", None) or index + 1)
            words = self._extract_words(getattr(utterance, "words", None))
            segments.append(
                SpeakerSegment(
                    speaker_id=speaker,
                    text=(getattr(utterance, "text", "") or "").strip(),
                    start_ms=self._as_int(getattr(utterance, "start", None)),
                    end_ms=self._as_int(getattr(utterance, "end", None)),
                    confidence=self._as_float(getattr(utterance, "confidence", None)),
                    words=words,
                )
            )

        if segments:
            return segments

        text = (getattr(transcript, "text", "") or "").strip()
        if not text:
            return []

        return [
            SpeakerSegment(
                speaker_id="1",
                text=text,
                start_ms=0,
                end_ms=self._duration_ms_from_transcript(transcript),
                words=self._extract_words(getattr(transcript, "words", None)),
            )
        ]

    def _extract_words(self, words_data: Any) -> list[WordTiming]:
        words: list[WordTiming] = []
        for word in words_data or []:
            words.append(
                WordTiming(
                    text=(getattr(word, "text", None) or getattr(word, "word", "") or "").strip(),
                    start_ms=self._as_int(getattr(word, "start", None)),
                    end_ms=self._as_int(getattr(word, "end", None)),
                    confidence=self._as_float(getattr(word, "confidence", None)),
                )
            )
        return words

    def _extract_duration_seconds(self, transcript: Any) -> float | None:
        audio_duration = getattr(transcript, "audio_duration", None)
        if audio_duration is not None:
            return self._as_float(audio_duration)

        duration_ms = self._duration_ms_from_transcript(transcript)
        if duration_ms is None:
            return None
        return duration_ms / 1000.0

    def _duration_ms_from_transcript(self, transcript: Any) -> int | None:
        utterances = getattr(transcript, "utterances", None) or []
        if utterances:
            last_end = getattr(utterances[-1], "end", None)
            return self._as_int(last_end)
        return None

    def _extract_confidence(
        self,
        transcript: Any,
        segments: list[SpeakerSegment],
    ) -> float | None:
        direct_confidence = self._as_float(getattr(transcript, "confidence", None))
        if direct_confidence is not None:
            return direct_confidence

        confidences = [
            segment.confidence for segment in segments if segment.confidence is not None
        ]
        if not confidences:
            return None
        return sum(confidences) / len(confidences)

    def _build_raw_response_snapshot(self, transcript: Any) -> dict[str, Any]:
        return {
            "id": getattr(transcript, "id", None),
            "status": str(getattr(transcript, "status", None)),
            "language_code": getattr(transcript, "language_code", None),
            "text": getattr(transcript, "text", None),
        }

    @staticmethod
    def _as_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
