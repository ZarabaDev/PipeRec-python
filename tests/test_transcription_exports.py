import unittest

from src.transcription.exporters import build_exported_meeting_report, validate_visation_payload
from src.transcription.models import SpeakerSegment, TranscriptionMetadata, TranscriptionResult


class TranscriptionExportTests(unittest.TestCase):
    def setUp(self):
        self.result = TranscriptionResult(
            status="completed",
            text="Locutor A: Oi\nLocutor B: Ola",
            metadata=TranscriptionMetadata(
                provider="assemblyai",
                model="universal",
                language="pt",
                audio_path="recordings/sample.mp3",
                duration_seconds=12.5,
                speaker_count=2,
            ),
            segments=[
                SpeakerSegment("A", "Oi", start_ms=0, end_ms=1000),
                SpeakerSegment("B", "Ola", start_ms=1000, end_ms=2000),
            ],
        )

    def test_render_plain_text_with_timestamps(self):
        rendered = self.result.render_plain_text(include_timestamps=True)
        self.assertIn("Locutor A", rendered)
        self.assertIn("00:00:00.000", rendered)

    def test_build_exported_report_keeps_legacy_payload(self):
        report = build_exported_meeting_report(
            self.result,
            {
                "contexto_e_objetivos": "Contexto",
                "pautas_discutidas": "* item",
                "combinados_e_prazos": "* prazo",
            },
            {
                "external_id": "20260312-1055",
                "title": "Reunião Visation - 2026-03-12 10:55",
                "started_at": "2026-03-12T10:55:00-03:00",
                "ended_at": "2026-03-12T11:51:07-03:00",
                "participants": ["Arthur", "Marco"],
                "source": "assemblyai-recorder",
            },
        )
        self.assertEqual(report.version, "2.0")
        self.assertEqual(report.legacy_payload["contexto_e_objetivos"], "Contexto")
        self.assertEqual(len(report.transcript["segments"]), 2)
        self.assertEqual(report.api_payload["external_id"], "20260312-1055")
        self.assertEqual(report.api_payload["participants"], ["Arthur", "Marco"])
        self.assertEqual(report.api_payload["transcript"], "Locutor A: Oi\nLocutor B: Ola")

    def test_validate_visation_payload_requires_strings(self):
        valid, error = validate_visation_payload(
            {
                "external_id": "20260312-1055",
                "title": "Daily Admin",
                "started_at": "2026-03-12T10:55:00-03:00",
                "ended_at": "2026-03-12T11:51:07-03:00",
                "participants": ["Arthur", "Marco"],
                "transcript": "Locutor A: Oi\nLocutor B: Ola",
                "source": "assemblyai-recorder",
            }
        )
        self.assertTrue(valid)
        self.assertIsNone(error)

        valid, error = validate_visation_payload(
            {
                "external_id": "20260312-1055",
                "title": "Daily Admin",
                "started_at": "2026-03-12T10:55:00-03:00",
                "ended_at": "2026-03-12T11:51:07-03:00",
                "participants": "Arthur, Marco",
                "transcript": "Locutor A: Oi\nLocutor B: Ola",
                "source": "assemblyai-recorder",
            }
        )
        self.assertFalse(valid)
        self.assertIn("participants", error)


if __name__ == "__main__":
    unittest.main()
