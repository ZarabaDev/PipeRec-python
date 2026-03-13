import os
import requests
from dotenv import load_dotenv

from src.transcription.exporters import validate_visation_payload


class ApiSender:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("VISATION_API_URL")
        self.internal_service = os.getenv("VISATION_INTERNAL_SERVICE", "community-backend")
        self.api_key = os.getenv("VISATION_API_KEY")
        self.available = bool(self.url and self.api_key)

    def send_report(self, report: dict) -> bool:
        if not self.available:
            print("ApiSender: URL ou chave da API não configuradas.")
            return False

        payload = self._select_payload(report)
        is_valid, error = validate_visation_payload(payload)
        if not is_valid:
            print(f"ApiSender: payload inválido para Visation: {error}")
            return False

        try:
            response = requests.post(
                self.url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Internal-Service": self.internal_service,
                    "X-Internal-Api-Key": self.api_key,
                },
                timeout=15,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"ApiSender: Erro ao enviar ata: {e}")
            return False

    def _select_payload(self, report: dict) -> dict:
        api_payload = report.get("api_payload")
        if isinstance(api_payload, dict):
            return api_payload
        return report
