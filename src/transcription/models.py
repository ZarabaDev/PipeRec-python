from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def format_timestamp_ms(value: int | None) -> str:
    if value is None:
        return "--:--:--.---"

    total_ms = max(0, int(value))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


@dataclass(slots=True)
class WordTiming:
    text: str
    start_ms: int | None = None
    end_ms: int | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SpeakerSegment:
    speaker_id: str
    text: str
    start_ms: int | None = None
    end_ms: int | None = None
    confidence: float | None = None
    words: list[WordTiming] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["start_hms"] = format_timestamp_ms(self.start_ms)
        payload["end_hms"] = format_timestamp_ms(self.end_ms)
        return payload

    @property
    def duration_ms(self) -> int | None:
        if self.start_ms is None or self.end_ms is None:
            return None
        return max(0, self.end_ms - self.start_ms)

    def render_line(self, include_timestamps: bool = True) -> str:
        prefix = f"Locutor {self.speaker_id}"
        if include_timestamps:
            return (
                f"[{format_timestamp_ms(self.start_ms)} - {format_timestamp_ms(self.end_ms)}] "
                f"{prefix}: {self.text}"
            )
        return f"{prefix}: {self.text}"


@dataclass(slots=True)
class TranscriptionMetadata:
    provider: str
    model: str | None = None
    language: str | None = None
    audio_path: str | None = None
    duration_seconds: float | None = None
    speaker_count: int | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TranscriptionResult:
    status: str
    text: str
    metadata: TranscriptionMetadata
    segments: list[SpeakerSegment] = field(default_factory=list)
    error: str | None = None
    confidence: float | None = None
    raw_response: dict[str, Any] | None = None

    @classmethod
    def failed(
        cls,
        provider: str,
        error: str,
        *,
        audio_path: str | None = None,
        model: str | None = None,
    ) -> "TranscriptionResult":
        return cls(
            status="error",
            text="",
            metadata=TranscriptionMetadata(
                provider=provider,
                model=model,
                audio_path=audio_path,
            ),
            error=error,
        )

    @property
    def ok(self) -> bool:
        return self.status == "completed" and not self.error

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "text": self.text,
            "metadata": self.metadata.to_dict(),
            "segments": [segment.to_dict() for segment in self.segments],
            "error": self.error,
            "confidence": self.confidence,
            "raw_response": self.raw_response,
        }

    def render_plain_text(self, include_timestamps: bool = False) -> str:
        if self.segments:
            return "\n".join(
                segment.render_line(include_timestamps=include_timestamps)
                for segment in self.segments
            )
        return self.text.strip()

    def preview_text(self, max_chars: int = 300) -> str:
        source_text = self.render_plain_text(include_timestamps=True).strip()
        if len(source_text) <= max_chars:
            return source_text
        return source_text[:max_chars].rstrip() + "..."


@dataclass(slots=True)
class ExportedMeetingReport:
    version: str
    source: dict[str, Any]
    transcript: dict[str, Any]
    summary: dict[str, Any]
    legacy_payload: dict[str, Any]
    api_payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source": self.source,
            "transcript": self.transcript,
            "summary": self.summary,
            "legacy_payload": self.legacy_payload,
            "api_payload": self.api_payload,
        }
