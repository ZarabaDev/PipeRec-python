from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.transcription.models import ExportedMeetingReport, TranscriptionResult


def _replace_suffix(base_path: str, suffix: str) -> Path:
    path = Path(base_path)
    return path.with_suffix(suffix)


def save_text_transcript(base_path: str, result: TranscriptionResult) -> Path:
    output_path = _replace_suffix(base_path, ".txt")
    output_path.write_text(
        result.render_plain_text(include_timestamps=True),
        encoding="utf-8",
    )
    return output_path


def save_rich_transcript(base_path: str, result: TranscriptionResult) -> Path:
    output_path = _replace_suffix(base_path, ".rich.json")
    output_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def build_exported_meeting_report(
    result: TranscriptionResult,
    summary: dict[str, Any],
    meeting_context: dict[str, Any] | None = None,
) -> ExportedMeetingReport:
    legacy_payload = {
        "contexto_e_objetivos": summary.get("contexto_e_objetivos", ""),
        "pautas_discutidas": summary.get("pautas_discutidas", ""),
        "combinados_e_prazos": summary.get("combinados_e_prazos", ""),
    }
    api_payload = (
        build_visation_api_payload(result, meeting_context)
        if meeting_context is not None
        else None
    )
    return ExportedMeetingReport(
        version="2.0",
        source={
            "provider": result.metadata.provider,
            "model": result.metadata.model,
            "language": result.metadata.language,
            "audio_path": result.metadata.audio_path,
            "speaker_count": result.metadata.speaker_count,
            "duration_seconds": result.metadata.duration_seconds,
        },
        transcript={
            "text": result.text,
            "segments": [segment.to_dict() for segment in result.segments],
        },
        summary=summary,
        legacy_payload=legacy_payload,
        api_payload=api_payload,
    )


def save_meeting_report(base_path: str, report: ExportedMeetingReport) -> Path:
    output_path = _replace_suffix(base_path, ".json")
    output_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def validate_visation_payload(payload: dict[str, Any]) -> tuple[bool, str | None]:
    required_keys = {
        "external_id",
        "title",
        "started_at",
        "ended_at",
        "participants",
        "transcript",
        "source",
    }
    missing = sorted(required_keys - payload.keys())
    if missing:
        return False, f"missing keys: {', '.join(missing)}"

    string_fields = {
        "external_id",
        "title",
        "started_at",
        "ended_at",
        "transcript",
        "source",
    }
    invalid = [key for key in string_fields if not isinstance(payload.get(key), str)]
    if invalid:
        return False, f"expected string values for: {', '.join(sorted(invalid))}"

    participants = payload.get("participants")
    if not isinstance(participants, list):
        return False, "participants must be a list"
    if any(not isinstance(item, str) for item in participants):
        return False, "participants must contain only strings"

    return True, None


def build_visation_api_payload(
    result: TranscriptionResult,
    meeting_context: dict[str, Any],
) -> dict[str, Any]:
    participants = meeting_context.get("participants") or []
    transcript_text = result.render_plain_text(include_timestamps=False).strip() or result.text.strip()

    return {
        "external_id": str(meeting_context.get("external_id", "")).strip(),
        "title": str(meeting_context.get("title", "")).strip(),
        "started_at": str(meeting_context.get("started_at", "")).strip(),
        "ended_at": str(meeting_context.get("ended_at", "")).strip(),
        "participants": [str(participant).strip() for participant in participants if str(participant).strip()],
        "transcript": transcript_text,
        "source": str(meeting_context.get("source", "")).strip(),
    }
