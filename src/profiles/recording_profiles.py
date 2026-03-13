from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class RecordingProfile:
    nome: str
    usar_assemblyai: bool
    gerar_ata: bool
    enviar_telegram: bool
    enviar_api: bool
    chat_id_telegram: str | None
    participants: list[str] | None = None
    transcription_provider: str = "groq"
    fallback_provider: str | None = None
    export_rich_transcript: bool = True
    report_strategy: str = "none"

GRAVACAO_SIMPLES = RecordingProfile(
    nome="Gravação Simples",
    usar_assemblyai=False,
    gerar_ata=False,
    enviar_telegram=False,
    enviar_api=False,
    chat_id_telegram=None,
    transcription_provider="groq",
    fallback_provider=None,
    export_rich_transcript=True,
    report_strategy="none",
)

REUNIAO_VISATION = RecordingProfile(
    nome="Reunião Visation",
    usar_assemblyai=True,
    gerar_ata=False,
    enviar_telegram=False,
    enviar_api=False,
    chat_id_telegram=None,
    participants=["Gio", "Alvin", "Marco", "Carol", "Leo", "Arthur"],
    transcription_provider="assemblyai",
    fallback_provider="groq",
    export_rich_transcript=True,
    report_strategy="none",
)

ALL_PROFILES = [GRAVACAO_SIMPLES, REUNIAO_VISATION]
