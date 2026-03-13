import os
import requests
from dotenv import load_dotenv

class TelegramSender:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.available = bool(self.token)

    def _split_message(self, text, max_len=4000):
        if len(text) <= max_len:
            return [text]
        
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            
            # Find the nearest newline before max_len
            split_at = text.rfind('\n', 0, max_len)
            if split_at == -1:
                # No newline, split at max_len
                split_at = max_len
            
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip() # remove leading newline from next chunk
            
        return chunks

    def send_message(self, chat_id: str, text: str) -> bool:
        if not self.available:
            print("TelegramSender: Token não configurado.")
            return False

        if not chat_id:
            print("TelegramSender: Chat ID não fornecido.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        chunks = self._split_message(text)
        success = True

        for i, chunk in enumerate(chunks):
            try:
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                }
                response = requests.post(url, json=payload)
                response.raise_for_status()
            except Exception as e:
                print(f"TelegramSender: Erro ao enviar chunk {i+1}: {e}")
                success = False
        
        return success
