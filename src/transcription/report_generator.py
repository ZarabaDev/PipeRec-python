from __future__ import annotations

import json
import re
from typing import Any

from src.transcription.exporters import build_exported_meeting_report
from src.transcription.models import ExportedMeetingReport, TranscriptionResult


class ReportGenerator:
    """
    Generates structured meeting reports from rich transcription results.
    """

    def __init__(
        self,
        client,
        model: str = "google/gemini-2.5-flash",
        participants: list[str] | None = None,
    ):
        self.client = client
        self.model = model
        self.participants = participants

    def generate_detailed_report(
        self,
        transcription: TranscriptionResult | str,
        meeting_context: dict[str, Any] | None = None,
    ) -> ExportedMeetingReport:
        result = self._coerce_transcription(transcription)

        try:
            facts = self._run_analyst_agent(result)
            summary = self._run_structured_report_agent(result, facts)
            return build_exported_meeting_report(result, summary, meeting_context)
        except Exception as exc:
            print(f"❌ Report Generation Error: {exc}")
            fallback = {
                "contexto_e_objetivos": f"Erro na geração da ata: {exc}",
                "pautas_discutidas": "Não foi possível gerar as pautas.",
                "combinados_e_prazos": "Não foi possível gerar os combinados.",
            }
            return build_exported_meeting_report(result, fallback, meeting_context)

    def _coerce_transcription(
        self,
        transcription: TranscriptionResult | str,
    ) -> TranscriptionResult:
        if isinstance(transcription, TranscriptionResult):
            return transcription

        from src.transcription.models import TranscriptionMetadata

        return TranscriptionResult(
            status="completed",
            text=transcription,
            metadata=TranscriptionMetadata(provider="legacy"),
        )

    def _run_analyst_agent(self, result: TranscriptionResult) -> str:
        print("🕵️ Analyst Agent: extracting grounded facts from speaker segments...")
        prompt = """
        Você é um Analista de Reuniões. Extraia fatos verificáveis a partir da transcrição segmentada.

        Responda com bullets curtos contendo:
        - contexto da reunião
        - tópicos discutidos
        - argumentos relevantes por locutor
        - decisões explícitas
        - pendências
        - combinados e prazos, apenas quando realmente mencionados

        Regras críticas:
        - Use apenas o que está na transcrição.
        - Cite speaker IDs como "Locutor X".
        - Não invente nomes de pessoas.
        - Se algo não estiver claro, diga que não ficou explícito.
        """
        if self.participants:
            prompt += (
                "\nParticipantes esperados (apenas contexto, não usar para inferir nomes): "
                + ", ".join(self.participants)
            )

        return self._call_llm(
            system_prompt=prompt,
            user_prompt=self._build_transcript_context(result),
            temp=0.2,
        )

    def _run_structured_report_agent(
        self,
        result: TranscriptionResult,
        facts: str,
    ) -> dict[str, str]:
        print("✍️ Builder Agent: generating structured visation report...")
        prompt = """
        Você é um Secretário Executivo. Gere um JSON com exatamente estas chaves:
        - contexto_e_objetivos
        - pautas_discutidas
        - combinados_e_prazos

        Regras:
        - Cada valor deve ser string.
        - Seja fiel à transcrição e aos fatos analisados.
        - Em pautas_discutidas e combinados_e_prazos use bullets em Markdown.
        - Cite Locutor X quando a autoria da fala for importante.
        - Não invente prazos ou responsáveis.
        - Se não houver prazo explícito, escreva "Prazo: não explicitado".
        """

        raw_json = self._call_llm(
            system_prompt=prompt,
            user_prompt=(
                "FATOS EXTRAÍDOS:\n"
                f"{facts}\n\n"
                "TRANSCRIÇÃO ESTRUTURADA:\n"
                f"{self._build_transcript_context(result)}"
            ),
            temp=0.1,
            json_mode=True,
        )
        data = self._parse_report_json(raw_json)
        return {
            "contexto_e_objetivos": self._normalize_section_value(
                data.get("contexto_e_objetivos", "")
            ),
            "pautas_discutidas": self._normalize_section_value(
                data.get("pautas_discutidas", "")
            ),
            "combinados_e_prazos": self._normalize_section_value(
                data.get("combinados_e_prazos", "")
            ),
        }

    def _parse_report_json(self, raw_json: str) -> dict[str, Any]:
        candidates = [raw_json.strip()]
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", raw_json, flags=re.S)
        candidates.extend(fenced)

        if "{" in raw_json and "}" in raw_json:
            candidates.append(raw_json[raw_json.find("{"): raw_json.rfind("}") + 1])

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        repair_prompt = """
        Corrija o texto abaixo para um JSON válido.
        Preserve somente as chaves:
        - contexto_e_objetivos
        - pautas_discutidas
        - combinados_e_prazos
        Retorne apenas JSON válido.
        """
        repaired = self._call_llm(
            system_prompt=repair_prompt,
            user_prompt=raw_json,
            temp=0,
            json_mode=True,
        )
        return json.loads(repaired)

    def _normalize_section_value(self, value: Any) -> str:
        if isinstance(value, list):
            return "\n".join(f"- {str(item).strip()}" for item in value if str(item).strip())
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value).strip()

    def _build_transcript_context(self, result: TranscriptionResult) -> str:
        metadata = result.metadata
        header = [
            f"Provider: {metadata.provider}",
            f"Modelo: {metadata.model}",
            f"Idioma: {metadata.language}",
            f"Speaker count: {metadata.speaker_count}",
            f"Duração: {metadata.duration_seconds}",
        ]
        segments = result.segments or []
        rendered_segments = "\n".join(
            segment.render_line(include_timestamps=True) for segment in segments
        )
        return "\n".join(header) + "\n\nSEGMENTOS:\n" + rendered_segments

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temp: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temp,
            "max_tokens": 4096,
            "top_p": 1,
            "stream": False,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        completion = self.client.chat.completions.create(**kwargs)
        return completion.choices[0].message.content
