
import os
import requests
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Union

# Load environment variables
load_dotenv()

FALLBACK_MODEL = "openai/gpt-4o-mini"

class _Message:
    def __init__(self, content: str):
        self.content = content

class _Choice:
    def __init__(self, message: _Message):
        self.message = message

class _Response:
    def __init__(self, choices: List[_Choice]):
        self.choices = choices

class _Completions:
    def __init__(self, client):
        self.client = client

    def _post(self, payload: Dict[str, Any], headers: Dict[str, Any]) -> _Response:
        """Helper to send POST request and parse response."""
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return _Response(choices=[_Choice(message=_Message(content=content))])

    def create(self, **kwargs) -> _Response:
        """
        Mimics the interface of client.chat.completions.create(**kwargs)
        but sends the request to OpenRouter with automatic fallback.
        """
        if not self.client.api_key:
            raise ValueError("OpenRouter API Key not found. Please set OPENROUTER_API_KEY in .env")

        headers = {
            "Authorization": f"Bearer {self.client.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/zarabatana/flux_audio",
            "X-Title": "Flux Audio",
        }

        payload = {
            "model": kwargs.get("model"),
            "messages": kwargs.get("messages"),
            "temperature": kwargs.get("temperature"),
            "max_tokens": kwargs.get("max_tokens"),
            "top_p": kwargs.get("top_p"),
            "stream": kwargs.get("stream", False),
        }

        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]

        try:
            return self._post(payload, headers)

        except requests.exceptions.RequestException as e:
            # Check if it's a model-related error (404 or 400 with specific message)
            is_model_error = False
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code in [400, 404]:
                    try:
                        error_json = e.response.json()
                        error_str = str(error_json).lower()
                        if any(term in error_str for term in ["model", "not found", "invalid"]):
                            is_model_error = True
                    except:
                        # If not JSON, default to status code check
                        is_model_error = True

            if is_model_error:
                print(f"⚠️ Modelo primário '{payload['model']}' indisponível. Tentando fallback: {FALLBACK_MODEL}")
                payload["model"] = FALLBACK_MODEL
                try:
                    return self._post(payload, headers)
                except Exception as fallback_err:
                    raise RuntimeError(f"OpenRouter Fallback Error (Primary: {kwargs.get('model')}, Fallback: {FALLBACK_MODEL}): {fallback_err}")
            
            # If not a model error, or primary error without response object, re-raise as RuntimeError
            error_msg = f"OpenRouter API Error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - Details: {error_details}"
                except:
                    error_msg += f" - Status Code: {e.response.status_code}"
            
            raise RuntimeError(error_msg)

class _Chat:
    def __init__(self, client):
        self.completions = _Completions(client)

class OpenRouterClient:
    """
    A duck-typed client that mimics the interface of Groq/OpenAI clients
    but connects to OpenRouter.
    
    Usage:
        client = OpenRouterClient()
        if client.available:
            response = client.chat.completions.create(...)
            print(response.choices[0].message.content)
    """
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.available = bool(self.api_key)
        self.chat = _Chat(self)

if __name__ == "__main__":
    # Simple test
    client = OpenRouterClient()
    if client.available:
        print("✅ OpenRouter Client Initialized")
        try:
            print("Sending test request...")
            completion = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": "Say hello!"}]
            )
            print(f"Response: {completion.choices[0].message.content}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("⚠️ OPENROUTER_API_KEY not found.")
